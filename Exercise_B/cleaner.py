"""
Core cleaning and deduplication logic for the episode catalog pipeline.

Responsibilities:
  - Parse raw CSV rows into Episode objects
  - Apply corrections at the field level
  - Detect and resolve duplicate episodes
  - Produce a final clean list and a QualityReport
"""

import csv
import io
from typing import Dict, List, Optional, Tuple

from models import Episode, QualityReport
from utils import (
    normalize_for_comparison,
    normalize_string,
    parse_air_date,
    parse_number,
)

# ────────────────────────────────────────────────────────
# CSV column indices (0-based)
# ────────────────────────────────────────────────────────
COL_SERIES = 0
COL_SEASON = 1
COL_EPISODE = 2
COL_TITLE = 3
COL_DATE = 4

EXPECTED_COLUMNS = 5


def _score_episode(ep: Episode) -> Tuple:
    """
    Return a tuple used for selecting the 'best' duplicate.
    Higher values mean better quality.
    Priority (spec order):
      1. Has valid Air Date
      2. Has known Episode Title
      3. Has valid Season Number
      4. Has valid Episode Number
    """
    return (
        int(ep.is_air_date_known()),
        int(ep.is_title_known()),
        int(ep.has_valid_season()),
        int(ep.has_valid_episode_number()),
        -ep.source_line,   # tie-break: earlier in file wins (lower line = higher score)
    )


def _parse_row(
    row: List[str],
    line_number: int,
    report: QualityReport,
) -> Optional[Episode]:
    """
    Convert a raw CSV row into an Episode, applying all correction rules.
    Returns None if the record must be discarded.
    """
    # Pad to expected width in case trailing columns are missing
    while len(row) < EXPECTED_COLUMNS:
        row.append("")

    raw_series = normalize_string(row[COL_SERIES])
    raw_season = row[COL_SEASON].strip()
    raw_episode = row[COL_EPISODE].strip()
    raw_title = normalize_string(row[COL_TITLE])
    raw_date = row[COL_DATE].strip()

    # ── Rule: Series Name is required ──
    if not raw_series:
        report.discarded += 1
        report.discarded_no_series += 1
        return None

    corrections_on_this_row = 0

    # ── Season Number ──
    season_val, season_corrected = parse_number(raw_season)
    if season_val is None:
        season_number = 0  # missing → default 0 (not counted as correction) 
    elif season_val < 0:
        season_number = 0
        season_corrected = True
    else:
        season_number = season_val
    if season_corrected:
        corrections_on_this_row += 1
        report.corrected_season += 1

    # ── Episode Number ──
    episode_val, episode_corrected = parse_number(raw_episode)
    if episode_val is None:
        episode_number = 0 # missing → default 0 (not counted as correction)
    elif episode_val < 0:
        episode_number = 0
        episode_corrected = True
    else:
        episode_number = episode_val
    if episode_corrected:
        corrections_on_this_row += 1
        report.corrected_episode_number += 1

    # ── Episode Title ──
    if not raw_title:
        episode_title = "Untitled Episode"   # Missing title is not counted as a correction (it's just a default)
    else:
        episode_title = raw_title

    # ── Air Date ──
    air_date, date_corrected = parse_air_date(raw_date)
    if date_corrected:
        corrections_on_this_row += 1
        report.corrected_air_date += 1

    # ── Rule: Discard if Episode Number, Title AND Air Date are all missing ──
    ep_num_missing = episode_number == 0
    title_missing = episode_title == "Untitled Episode"
    date_missing = air_date == "Unknown"

    if ep_num_missing and title_missing and date_missing:
        report.discarded += 1
        report.discarded_no_identifying_info += 1
        return None

    if corrections_on_this_row > 0:
        report.corrected += 1

    return Episode(
        series_name=raw_series,
        season_number=season_number,
        episode_number=episode_number,
        episode_title=episode_title,
        air_date=air_date,
        source_line=line_number,
    )


def _dedup_key_season_episode(ep: Episode) -> Optional[Tuple]:
    """
    Key 1: (series_norm, season, episode_number) — when both are non-zero.
    """
    if ep.season_number != 0 and ep.episode_number != 0:
        return (
            normalize_for_comparison(ep.series_name),
            ep.season_number,
            ep.episode_number,
        )
    return None


def _dedup_key_zero_season(ep: Episode) -> Optional[Tuple]:
    """
    Key 2: (series_norm, 0, episode_number, title_norm) — season unknown.
    """
    if ep.season_number == 0 and ep.episode_number != 0:
        return (
            normalize_for_comparison(ep.series_name),
            0,
            ep.episode_number,
            normalize_for_comparison(ep.episode_title),
        )
    return None


def _dedup_key_zero_episode(ep: Episode) -> Optional[Tuple]:
    """
    Key 3: (series_norm, season, 0, title_norm) — episode number unknown.
    """
    if ep.episode_number == 0 and ep.season_number != 0:
        return (
            normalize_for_comparison(ep.series_name),
            ep.season_number,
            0,
            normalize_for_comparison(ep.episode_title),
        )
    return None


def deduplicate(episodes: List[Episode], report: QualityReport) -> List[Episode]:
    """
    Detect and resolve duplicate episodes according to deduplication rules.

    Each episode may match others via multiple keys; we use a union-find
    approach to group all episodes that share *any* key, then pick the best
    representative from each group.
    """

    n = len(episodes)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    # Build index: key → list of episode indices
    key_index: Dict[Tuple, List[int]] = {}

    for i, ep in enumerate(episodes):
        for key_fn in (_dedup_key_season_episode, _dedup_key_zero_season, _dedup_key_zero_episode):
            key = key_fn(ep)
            if key is not None:
                key_index.setdefault(key, []).append(i)

    # Union episodes sharing the same key
    for indices in key_index.values():
        for j in range(1, len(indices)):
            union(indices[0], indices[j])

    # Group by root
    groups: Dict[int, List[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    result: List[Episode] = []
    total_duplicates = 0

    for indices in groups.values():
        if len(indices) > 1:
            total_duplicates += len(indices) - 1  # extras are duplicates

        # Pick the best episode from each group
        best = max(indices, key=lambda i: _score_episode(episodes[i]))
        result.append(episodes[best])

    report.duplicates_detected = total_duplicates

    # Preserve original file order for readability
    result.sort(key=lambda ep: (
        normalize_for_comparison(ep.series_name),
        ep.season_number,
        ep.episode_number,
        ep.source_line,
    ))

    return result


def clean_catalog(
    csv_content: str,
    report: QualityReport,
) -> List[Episode]:
    """
    Full pipeline: parse → validate/correct → deduplicate.

    Args:
        csv_content: raw text of the input CSV file
        report:      QualityReport instance to fill in

    Returns:
        List of clean, deduplicated Episode objects
    """
    reader = csv.reader(io.StringIO(csv_content))

    episodes: List[Episode] = []
    line_number = 0

    for row in reader:
        line_number += 1

        # Skip header row if present
        if line_number == 1:
            first = row[0].strip().lower() if row else ""
            if first in ("series name", "seriesname", "series_name", "name"):
                continue

        report.total_input += 1

        episode = _parse_row(row, line_number, report)
        if episode is not None:
            episodes.append(episode)

    clean = deduplicate(episodes, report)
    report.total_output = len(clean)

    return clean
