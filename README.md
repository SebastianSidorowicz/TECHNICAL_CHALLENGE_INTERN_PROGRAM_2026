# Proofpoint Internship Program 2026 — Technical Challenge

This repository contains my solutions for the Proofpoint 2026 Intern Program technical challenge.

---

## Repository Structure

```
TECHNICAL-CHALLENGE-INTERN-PROGRAM-2026/
│
├── Exercise_A/                         # Written questions
│   └── answers.md
│   └── answers.pdf                 #It's the same as answers.md but in .pdf format 
│
├── Exercise_B/                     # The Streaming Service's Lost Episodes
│   ├── models.py                   # Data models: Episode, QualityReport
│   ├── utils.py                    # Field normalization and validation
│   │── cleaner.py                  # Cleaning and deduplication logic
│   ├── main.py                     # Entry point
│   └── README.md
│
├── Exercise_C/                         # Word Frequency Analyzer
│   └── word_frequency.py
│
└── TECHNICAL_CHALLENGE_INTERN_PROGRAM_2026.pdf
```

---

## Exercise A — Written Questions

Personal responses to the three questions about programming background, teamwork experience, and technical development plans.

See [`Exercise_A/answers.md`](Exercise_A/answers.md)

---

## Exercise B — The Streaming Service's Lost Episodes

### Overview

A streaming platform's episode catalog was ingested without any validation, resulting in missing data, invalid formats, and duplicate entries. This program reads the raw CSV, cleans every field, deduplicates episodes, and produces a corrected catalog alongside a data quality report.

### Requirements

- Python 3.10+
- No external dependencies — standard library only

### How to Run

```bash
cd Exercise_B
python /main.py <input_csv> --output-dir <output_folder>
```

**Example:**

```bash
python main.py input.csv --output-dir .\output
```

**Output files:**

| File | Description |
|------|-------------|
| `episodes_clean.csv` | Cleaned and deduplicated episode catalog |
| `report.md` | Data quality report with correction and deduplication stats |


```bash
cd Exercise_B
python components/main.py test_input.csv --output-dir output/
```

### Input Format

The input CSV must have columns in this order — with or without a header row:

```
Series Name, Season Number, Episode Number, Episode Title, Air Date
```

### Correction Rules

| Field | Rule |
|-------|------|
| Series Name | Required — records without it are discarded |
| Season Number | Must be a plain integer ≥ 0. Anything else → `0` |
| Episode Number | Must be a plain integer ≥ 0. Anything else → `0` |
| Episode Title | Missing → `"Untitled Episode"` |
| Air Date | Must be a recognizable date → normalized to `YYYY-MM-DD`. Invalid → `"Unknown"` |
| Episode Number + Title + Air Date all missing | Record is discarded |

**Accepted date formats** (all normalized to `YYYY-MM-DD`):

| Input | Output |
|-------|--------|
| `2022-05-03` | `2022-05-03` |
| `2022/5/3` | `2022-05-03` |
| `03/05/2022` | `2022-05-03` |
| `03-05-2022` | `2022-05-03` |
| `not a date` | `Unknown` |

### Deduplication Strategy

Episodes are grouped as duplicates when they share **any** of these composite keys (all comparisons are normalized: trimmed, collapsed whitespace, lowercased):

| Key | Condition | Fields compared |
|-----|-----------|-----------------|
| K1 | `season ≠ 0` AND `episode ≠ 0` | `series`, `season`, `episode` |
| K2 | `season = 0` AND `episode ≠ 0` | `series`, `0`, `episode`, `title` |
| K3 | `episode = 0` AND `season ≠ 0` | `series`, `season`, `0`, `title` |


When duplicates are found, the **best** record is kept using this priority:

1. Valid Air Date over `"Unknown"`
2. Known Episode Title over `"Untitled Episode"`
3. Valid Season Number (≠ 0)
4. Valid Episode Number (≠ 0)
5. Earliest occurrence in the source file (tie-breaker)

### Example

**Input:**
```csv
Series Name,Season Number,Episode Number,Episode Title,Air Date
Breaking Bad,1,1,Pilot,2008-01-20
Breaking Bad,1,1,Pilot,not a date
Lost,one,2,Pilot Part 2,2004/9/29
,1,1,Some Episode,2020-01-01
```

**Output** (`episodes_clean.csv`):
```csv
SeriesName,SeasonNumber,EpisodeNumber,EpisodeTitle,AirDate
Breaking Bad,1,1,Pilot,2008-01-20
Lost,0,2,Pilot Part 2,2004-09-29
```

**Report summary** (`report.md`):
```
Total input records : 4
Total output records: 2
Discarded           : 1   (missing Series Name)
Corrected           : 2   (season "one" → 0, date "2004/9/29" → 2004-09-29)
Duplicates detected : 1
```

---

## Exercise C — Word Frequency Analyzer

### Overview

Reads any plain text file and prints the top-10 most frequent words, case-insensitively and ignoring punctuation and special characters.

### How to Run

```bash
cd Exercise_C
python word_frequency.py <text_file>
```

**Example:**

```bash
python word_frequency.py example.txt
```

**Optional — change the number of top words displayed:**

```bash
python word_frequency.py sample.txt --top 20
```

### Example Output

```
[INFO] File     : sample.txt
[INFO] Total unique words: 312
[INFO] Top 10 most frequent words:

Rank   Word                      Frequency
-------------------------------------------
1      the                             148
2      and                              96
3      of                               81
4      to                               74
5      a                                63
...
```

---

## Requirements

- Python 3.10+
- Standard library only — no `pip install` needed