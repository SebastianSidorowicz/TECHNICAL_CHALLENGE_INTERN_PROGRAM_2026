"""
Data models for the Streaming Service Episode Catalog.
Defines the Episode dataclass and related types used across the pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Episode:
    """Represents a single episode entry in the catalog."""

    series_name: str
    season_number: int
    episode_number: int
    episode_title: str
    air_date: str

    # Internal tracking fields (not written to output)
    source_line: int = field(default=0, repr=False)

    def is_air_date_known(self) -> bool:
        return self.air_date != "Unknown"

    def is_title_known(self) -> bool:
        return self.episode_title != "Untitled Episode"

    def has_valid_season(self) -> bool:
        return self.season_number != 0

    def has_valid_episode_number(self) -> bool:
        return self.episode_number != 0


@dataclass
class QualityReport:
    """Accumulates statistics about the cleaning/deduplication process."""

    total_input: int = 0
    total_output: int = 0
    discarded: int = 0
    corrected: int = 0
    duplicates_detected: int = 0

    # Detailed breakdown counters
    discarded_no_series: int = 0
    discarded_no_identifying_info: int = 0
    corrected_season: int = 0
    corrected_episode_number: int = 0
    corrected_title: int = 0
    corrected_air_date: int = 0
