#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data cleaning for the movie survey data.

Real survey data is messy. The same movie shows up as "Avengers: Endgame",
"avengers endgame", "Avengers End Game" and "Avenger's Endgame". If we don't
clean it, the graph treats those as four different movies, and the
recommendations get worse -- four weak nodes instead of one strong one.

The approach here is the standard one:

  1. Build a *matching key* for each title -- an aggressively normalized
     string we only ever use for comparison, never for display.
  2. Group the raw titles by that key.
  3. Pick the nicest-looking raw title in each group as the *display name*.

So "Avengers: Endgame" and "avengers endgame" both get the key
"avengers endgame", and the group displays as "Avengers: Endgame".
"""
import re
import unicodedata
from collections import Counter

# Words that stay lowercase in a title, unless they're the first or last word.
SMALL_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
    "nor", "of", "on", "onto", "or", "the", "to", "vs", "with",
}

# Values people type when they mean "nothing here".
NULL_VALUES = {"", "na", "n/a", "nan", "none", "null", "-", "--", "x", "?"}

# Straight-quote replacements for the curly characters phones insert.
UNICODE_FIXES = {
    "‘": "'", "’": "'",           # curly single quotes
    "“": '"', "”": '"',           # curly double quotes
    "–": "-", "—": "-",           # en/em dashes
    "…": "...",                        # ellipsis
    " ": " ",                          # non-breaking space
}


def _fix_unicode(text):
    """Replace curly quotes/dashes with plain ASCII equivalents."""
    # NFKC folds lookalike characters (full-width letters, ligatures) together.
    text = unicodedata.normalize("NFKC", text)
    for weird, plain in UNICODE_FIXES.items():
        text = text.replace(weird, plain)
    return text


def clean_title(raw, merge_articles=False):
    """Return the matching key for a raw movie title.

    The key is lowercase, punctuation-free and single-spaced, so all the
    cosmetic ways of writing one title collapse onto each other. Returns ""
    for blanks and junk, which the caller should skip.

    merge_articles=True also drops a leading "the"/"a"/"an", so "The Avengers"
    matches "Avengers". That's off by default because it over-merges: "The
    Batman" (2022) and "Batman" (1989) really are different movies.
    """
    # Survey rows can hand us floats (pandas NaN), numbers, or None.
    if raw is None:
        return ""
    text = _fix_unicode(str(raw))

    # Drop wrapping quotes: people paste titles as "The Phoenix Reborn".
    text = text.strip().strip('"').strip("'").strip()

    # Drop parenthetical asides: "Back to the Future (1985)", "Avatar (blue
    # people one)". If the whole title was in parens -- "(kongfu panda)" --
    # keep the inside instead of throwing everything away.
    without_parens = re.sub(r"\([^)]*\)", " ", text)
    if without_parens.strip():
        text = without_parens

    text = text.lower()

    # Catch "n/a" and friends now, before the punctuation step below turns
    # them into innocent-looking strings like "n a".
    if text in NULL_VALUES:
        return ""

    # "&" and "and" are the same word to a human, so make them the same
    # word to us.
    text = text.replace("&", " and ")

    # Delete apostrophes rather than spacing them out, so "Avenger's" becomes
    # "avengers" and matches "Avengers". Spacing would give "avenger s".
    text = text.replace("'", "")

    # Strip every character that isn't a letter, digit or space. This is what
    # merges "Avengers: Endgame"/"Avengers Endgame", "Dr. Strange"/"Dr Strange"
    # and "Freddy's"/"Freddys". \w keeps non-Latin scripts intact, so titles
    # written in Chinese or Japanese survive this step.
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)

    # Collapse the runs of spaces the steps above just created.
    text = re.sub(r"\s+", " ", text).strip()

    if merge_articles:
        text = re.sub(r"^(the|a|an)\s+", "", text)

    if text in NULL_VALUES:
        return ""

    # "???" and friends normalize to nothing useful. Note this test is
    # Unicode-aware: 白雪公主 is alphanumeric, so real titles are kept.
    if not any(char.isalnum() for char in text):
        return ""

    return text


def smart_title_case(text):
    """Capitalize a title the way a person would.

    str.title() gets this wrong twice over: it lowercases the interior of
    names ("DaQuan" -> "Daquan") and it capitalizes words that shouldn't be
    ("Lord Of The Rings"). This handles the small words and leaves any word
    that already has an interior capital alone.
    """
    words = text.split()
    result = []
    for i, word in enumerate(words):
        is_edge = (i == 0 or i == len(words) - 1)
        if any(char.isupper() for char in word[1:]):
            # Already styled by the person who typed it: "McDonald", "iRobot".
            result.append(word)
        elif word.lower() in SMALL_WORDS and not is_edge:
            result.append(word.lower())
        else:
            result.append(word[:1].upper() + word[1:].lower())
    return " ".join(result)


def _display_score(raw, count):
    """Rank a raw spelling as a candidate display name. Higher wins.

    Preference order, most important first:
      1. How often people typed it that way -- the crowd is usually right.
      2. Not being SHOUTED ("Coco" beats "COCO").
      3. Having real capitalization ("Avengers endgame" beats "avengers endgame").
      4. Keeping punctuation ("Avengers: Endgame" beats "Avengers Endgame").
      5. Length, then alphabetical, purely so the result is deterministic.
    """
    letters = [char for char in raw if char.isalpha()]
    is_shouted = len(letters) > 3 and all(char.isupper() for char in letters)
    capitals = sum(1 for char in raw if char.isupper())
    punctuation = sum(1 for char in raw if not char.isalnum() and not char.isspace())
    return (count, not is_shouted, capitals, punctuation, len(raw), raw)


def clean_name(raw):
    """Clean a person's name: trim, collapse spaces, fix obvious casing.

    Casing is only corrected when the name is entirely lower or entirely
    upper case. "DaQuan" and "McKenna" are left exactly as typed.
    """
    if raw is None:
        return ""
    name = re.sub(r"\s+", " ", _fix_unicode(str(raw)).strip())
    if not name or name.lower() in NULL_VALUES:
        return ""
    # Someone typed "'-" instead of a name. No letters or digits, no person.
    if not any(char.isalnum() for char in name):
        return ""
    if name.islower() or name.isupper():
        # Lowercase first: smart_title_case leaves words with interior
        # capitals alone, so "RUSH" would otherwise pass straight through.
        name = smart_title_case(name.lower())
    return name


class TitleCleaner:
    """Groups the raw spellings of each title and picks one to display.

    Usage is two passes over the data -- feed it everything first, then ask
    for display names once it has seen all the variants:

        cleaner = TitleCleaner()
        for title in every_raw_title:
            cleaner.add(title)

        key = cleaner.key("avengers endgame")
        cleaner.display(key)   # -> "Avengers: Endgame"
    """

    def __init__(self, merge_articles=False):
        self.merge_articles = merge_articles
        # key -> Counter of the raw spellings seen for it
        self.variants = {}

    def add(self, raw):
        """Record one raw title. Returns its key, or "" if it was junk."""
        key = self.key(raw)
        if key:
            self.variants.setdefault(key, Counter())[str(raw).strip()] += 1
        return key

    def key(self, raw):
        """The matching key for a raw title, with this cleaner's settings."""
        return clean_title(raw, merge_articles=self.merge_articles)

    def display(self, key):
        """The best-looking spelling for a key, title-cased if need be."""
        counts = self.variants.get(key)
        if not counts:
            # Never seen it -- fall back to tidying up the key itself.
            return smart_title_case(key)

        best = max(counts.items(), key=lambda item: _display_score(*item))[0]
        best = best.strip().strip('"').strip()

        # If the only spellings we have are all-lowercase or ALL-CAPS,
        # case it properly ourselves.
        letters = [char for char in best if char.isalpha()]
        is_shouted = len(letters) > 3 and all(char.isupper() for char in letters)
        if is_shouted or not any(char.isupper() for char in best):
            best = smart_title_case(best.lower())
        return best

    def display_for_raw(self, raw):
        """Convenience: raw title straight to its display name."""
        return self.display(self.key(raw))

    def report(self):
        """Summary of what the cleaning actually merged.

        Handy for the lecture: it shows the messiest titles in the data.
        """
        total_raw = sum(sum(counts.values()) for counts in self.variants.values())
        distinct_raw = sum(len(counts) for counts in self.variants.values())
        merged = sorted(
            (
                (len(counts), self.display(key), sorted(counts))
                for key, counts in self.variants.items()
                if len(counts) > 1
            ),
            reverse=True,
        )
        return {
            "titles_read": total_raw,
            "distinct_spellings": distinct_raw,
            "distinct_movies": len(self.variants),
            "merged": merged,
        }


def main():
    """Show what the cleaning does to the real survey data."""
    import csv

    with open("movies_data.csv", "r", encoding="utf-8-sig") as infile:
        rows = list(csv.DictReader(infile))

    movie_columns = [name for name in rows[0] if name.lower().startswith("movie ")]

    cleaner = TitleCleaner()
    for row in rows:
        for column in movie_columns:
            cleaner.add(row[column])

    stats = cleaner.report()
    print(f"Read {stats['titles_read']} titles")
    print(f"  {stats['distinct_spellings']} distinct spellings")
    print(f"  {stats['distinct_movies']} actual movies after cleaning")
    print("\nMessiest titles in the data:")
    for count, display, spellings in stats["merged"][:10]:
        print(f"  {display}  ({count} spellings)")
        print(f"    {spellings}")


if __name__ == "__main__":
    main()
