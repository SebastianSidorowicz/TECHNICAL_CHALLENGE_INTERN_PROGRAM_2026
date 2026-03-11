"""
Word Frequency Analyzer — Bonus Exercise

Reads a text file and prints the top-10 most frequent words,
case-insensitively and ignoring punctuation / special characters.

Usage:
    python word_frequency.py <text_file>

Example:
    python word_frequency.py 'lore ipsum.txt' 
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


def count_words(text: str) -> Counter:
    """
    Tokenize text into words and count occurrences.

    - Converts to lowercase
    - Strips punctuation and special characters
    - Ignores empty tokens
    """
    # Keep only letters, digits, and whitespace; then split
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    words = cleaned.split()
    return Counter(words)


def display_top_n(counter: Counter, n: int = 10) -> None:
    """Print the top-N most frequent words in a formatted table."""
    top = counter.most_common(n)
    print(f"\n{'Rank':<6} {'Word':<25} {'Frequency':>10}")
    print("-" * 43)
    for rank, (word, freq) in enumerate(top, start=1):
        print(f"{rank:<6} {word:<25} {freq:>10}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count word frequencies in a text file and show the top 10."
    )
    parser.add_argument("text_file", help="Path to the input text file.")
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top words to display (default: 10).",
    )
    args = parser.parse_args()

    path = Path(args.text_file)
    if not path.is_file():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8", errors="replace")
    counter = count_words(text)
    
    if not counter:
        print("\n\033[1;31m[WARNING] No words were found in the file.\033[0m\n")
        sys.exit(0)

    print(f"[INFO] File     : {path}")
    print(f"[INFO] Total unique words: {len(counter)}")
    print(f"[INFO] Top {args.top} most frequent words:")
    display_top_n(counter, n=args.top)


if __name__ == "__main__":
    main()
