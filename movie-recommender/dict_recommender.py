""" Recommendation System. """
from collections import Counter
import pandas as pd

from clean import TitleCleaner

# Load the dataset into a dataframe
data_df = pd.read_csv("movies_data.csv", encoding="utf-8-sig")

# columns I care about
mov_cols = ["Movie 1", "Movie 2", "Movie 3", "Movie 4",
            "Movie 5", "Movie 6", "Movie 7", "Movie 8",
            "Movie 9", "Movie 10"]

# Access the data row by row
data_lst = data_df.to_dict(orient="records")

# First pass: let the cleaner see every title so it can group the spellings.
# Without this, "Harry Potter", "harry potter" and "harry potter " are three
# different keys, and each one only gets a third of the co-occurrences.
cleaner = TitleCleaner()
for row in data_lst:
    for mov_col in mov_cols:
        cleaner.add(row[mov_col])

# create the cooccurrences dictionary
co_occurrences_dct: dict[str, list[str]] = {}

# Second pass: build the co-occurrences out of the cleaned names.
for row in data_lst:
    # pull out the movies and create a list
    # of movies that the person has listed.
    mov_lst: list[str] = []
    for mov_col in mov_cols:
        movie = row[mov_col]
        if pd.notna(movie):
            # Blank and junk entries clean to "", so skip those.
            key = cleaner.key(movie)
            if key:
                mov_lst = mov_lst + [cleaner.display(key)]

    # A person can list the same movie twice under two spellings; after
    # cleaning those are one movie, so don't double-count them.
    mov_lst = list(dict.fromkeys(mov_lst))

    # for every movie in that list,
    # add the list to the dictionary entry for that movie
    # (tracking co-occurrences)
    for movie in mov_lst:
        co_occurrences_dct[movie] = co_occurrences_dct.get(movie, []) + mov_lst


def recommend(movie, how_many=10):
    """Recommend movies for people who liked this one.

    The lookup is cleaned too, so it doesn't matter whether you ask for
    "harry potter", "Harry Potter" or "HARRY POTTER".
    """
    key = cleaner.display(cleaner.key(movie))
    if key not in co_occurrences_dct:
        return []

    counts = Counter(co_occurrences_dct[key])
    # The movie is in every one of its own co-occurrence lists, so it would
    # always come out on top. Drop it before ranking.
    del counts[key]
    return counts.most_common(how_many)


if __name__ == "__main__":
    print(recommend("harry potter"))
