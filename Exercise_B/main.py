"""
Main entry point for the Streaming Service Episode Catalog Cleaner.

Usage:
    python main.py <input_csv> [--output-dir <dir>]
    
Example:
    python main.py test_input.csv --output-dir .\output

Outputs:
    episodes_clean.csv  — cleaned and deduplicated episode catalog
    report.md           — data quality report
"""

import argparse
import csv
import os
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cleaner import clean_catalog
from models import Episode, QualityReport


# ───────────────────────────────────
# Output writers
# ───────────────────────────────────

def write_clean_csv(episodes: list[Episode], output_path: str) -> None:
    """Write the cleaned episode list to a CSV file."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["SeriesName", "SeasonNumber", "EpisodeNumber", "EpisodeTitle", "AirDate"])
        for ep in episodes:
            writer.writerow([
                ep.series_name,
                ep.season_number,
                ep.episode_number,
                ep.episode_title,
                ep.air_date,
            ])


def write_report(report: QualityReport, output_path: str) -> None:
    """Generate the Markdown data quality report."""
    dedup_explanation = textwrap.dedent("""\
        ## Deduplication Strategy

        Episodes are grouped as duplicates when they share **any** of the following
        composite keys (all string comparisons are normalized: trimmed, collapsed
        whitespace, lowercased):

        | Key | When applied | Fields compared |
        |-----|-------------|-----------------|
        | **K1** | Season ≠ 0 AND Episode ≠ 0 | `series_name`, `season_number`, `episode_number` |
        | **K2** | Season = 0 AND Episode ≠ 0 | `series_name`, `0`, `episode_number`, `episode_title` |
        | **K3** | Episode = 0 AND Season ≠ 0 | `series_name`, `season_number`, `0`, `episode_title` |

        A **union-find** (disjoint-set) structure groups episodes that share *any*
        key across all three rules, so transitive duplicates are also resolved.

        From each duplicate group, the **best** representative is selected using
        this priority order:
        1. Episode with a **known Air Date** over `"Unknown"`
        2. Episode with a **known Title** over `"Untitled Episode"`
        3. Episode with a **valid Season Number** (≠ 0)
        4. Episode with a **valid Episode Number** (≠ 0)
        5. **Earliest occurrence** in the source file (tie-breaker)
    """)

    content = textwrap.dedent(f"""\
        # Data Quality Report

        ## Summary

        | Metric | Count |
        |--------|-------|
        | Total input records | {report.total_input} |
        | Total output records | {report.total_output} |
        | Discarded entries | {report.discarded} |
        | Corrected entries | {report.corrected} |
        | Duplicates detected | {report.duplicates_detected} |

        ## Discarded Entries Breakdown

        | Reason | Count |
        |--------|-------|
        | Missing Series Name | {report.discarded_no_series} |
        | Episode Number, Title AND Air Date all missing | {report.discarded_no_identifying_info} |
        | **Total discarded** | **{report.discarded}** |

        ## Corrections Breakdown

        | Field corrected | Count |
        |----------------|-------|
        | Season Number | {report.corrected_season} |
        | Episode Number | {report.corrected_episode_number} |
        | Air Date | {report.corrected_air_date} |
        | *(Episode title defaults are not counted as corrections)* | — |

        > **Note:** A single row may have multiple fields corrected, but is counted
        > only once in the total corrected rows figure.

        ---

        {dedup_explanation}
    """)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


# ───────────────────────────────────
# CLI
# ───────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean and deduplicate a streaming-service episode catalog CSV."
    )
    parser.add_argument(
        "input_csv",
        help="Path to the raw input CSV file.",
    )
    parser.add_argument(
        "--output-dir",
        default=".\output",
        help="Directory where output files will be written (default: current dir).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = args.input_csv
    output_dir = args.output_dir

    # ── Read input ─────────────────────────────────────────────────────────────
    if not os.path.isfile(input_path):
        print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Reading input file: {input_path}")
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        csv_content = f.read()

    # ── Clean ──────────────────────────────────────────────────────────────────
    report = QualityReport()
    episodes = clean_catalog(csv_content, report)

    # ── Write outputs ──────────────────────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)

    clean_csv_path = os.path.join(output_dir, "episodes_clean.csv")
    report_path = os.path.join(output_dir, "report.md")

    write_clean_csv(episodes, clean_csv_path)
    write_report(report, report_path)

    # ── Console summary ────────────────────────────────────────────────────────
    print(f"[INFO] Done.")
    print(f"       Input records   : {report.total_input}")
    print(f"       Output records  : {report.total_output}")
    print(f"       Discarded       : {report.discarded}")
    print(f"       Corrected       : {report.corrected}")
    print(f"       Duplicates found: {report.duplicates_detected}")
    print(f"[INFO] Output written to: {output_dir}/")
    print(f"         → {clean_csv_path}")
    print(f"         → {report_path}")


if __name__ == "__main__":
    main()
