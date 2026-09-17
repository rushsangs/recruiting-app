#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  4 14:03:38 2025

@author: Rush Sanghrajka
DS2000 Section 3
Recommender system
"""
import csv

from graph import Graph
from collections import Counter
from clean import TitleCleaner, clean_name
class Recommender:

    def __init__(self, merge_articles=False):
        self.graph = Graph()
        self.people = []
        self.movies = []
        # Handles the messy-title problem: see clean.py.
        self.cleaner = TitleCleaner(merge_articles=merge_articles)

    def read_csv(self, filename):
        '''Reads the csv file into a list of lists.
        '''
        data = []

        # Use the csv module rather than split(","). Some titles contain a
        # comma -- "Crazy, Stupid Love" -- and the survey tool quotes those.
        # Splitting on every comma tears them in half and shifts every later
        # column over, so people end up connected to the wrong movies.
        # encoding="utf-8-sig" drops the byte-order mark spreadsheets add.
        with open(filename, "r", encoding="utf-8-sig", newline="") as infile:
            reader = csv.reader(infile)

            # skip the header
            next(reader, None)
            for row_data in reader:
                # Ignore fully blank lines at the end of the file.
                if any(cell.strip() for cell in row_data):
                    data.append(row_data)

        return data

    def add_to_graph(self, data_lst):
        ''' Will add the data from list of lists to
        my graph. First entry in the row is person's
        name and after that we have 10 movies.
        '''
        # First pass: show every title to the cleaner so it can group the
        # spellings and work out the nicest one to display for each movie.
        # We can't name the nodes until it has seen the whole file.
        for row in data_lst:
            for movie_name in row[2:12]:
                self.cleaner.add(movie_name)

        # Every movie name that will end up in the graph. We need this to
        # spot people whose name is also a movie title (see below).
        movie_names = {self.cleaner.display(key) for key in self.cleaner.variants}

        # Second pass: build the graph using the cleaned names.
        for row in data_lst:
            # A row that got cut short has no name to attach movies to.
            if len(row) < 2:
                continue

            # name is location 1
            person_name = clean_name(row[1])
            if not person_name:
                continue

            # The graph uses the name as the node, so a person and a movie
            # with the same name become one node -- and then the movie
            # "Interstellar" inherits the movies of the student named
            # Interstellar. Real collisions in this data: Emma, Lucy,
            # Annabelle, Spencer, Interstellar, Superbad. Label the person.
            if person_name in movie_names:
                person_name = person_name + " (student)"

            self.graph.add_node(person_name)
            if person_name not in self.people:
                self.people.append(person_name)

            # now add movies which are the 10 other columns!
            for raw_movie in row[2:12]:
                # The key merges the spellings; the display name is what we
                # actually show. Blank and junk entries come back as "".
                movie_key = self.cleaner.key(raw_movie)
                if not movie_key:
                    continue

                movie_name = self.cleaner.display(movie_key)

                self.graph.add_node(movie_name)

                if movie_name not in self.movies:
                    self.movies.append(movie_name)

                # add edge
                self.graph.add_edge(person_name, movie_name)

    def find_movie(self, movie):
        '''Look up a movie however it was typed.

        The graph is keyed by the cleaned display name, so "harry potter",
        "Harry Potter" and "harry potter " all need to land on the same node.
        Returns the node name, or None if we don't have that movie.
        '''
        movie_name = self.cleaner.display(self.cleaner.key(movie))
        if movie_name in self.movies:
            return movie_name
        return None

    def find_person(self, person):
        '''Look up a person however their name was typed.'''
        person_name = clean_name(person)
        if person_name in self.people:
            return person_name

        # People whose name clashed with a movie got labelled in add_to_graph.
        if person_name + " (student)" in self.people:
            return person_name + " (student)"

        # Fall back to a case-insensitive match, in case the roster spelling
        # differs from what was typed ("daquan" -> "DaQuan").
        for known in self.people:
            if known.lower() == person_name.lower():
                return known
        return None

    def get_liked_movies(self, person):
        '''Return a list of movies the person likes.'''
        return self.graph.get_neighbors(self.find_person(person) or person)

    def get_movie_likers(self, movie):
        ''' Return a list of people who like the movie.'''
        return self.graph.get_neighbors(self.find_movie(movie) or movie)

    def recommend(self, person):
        '''Recommend some movies to a person.
        '''
        # Resolve the name first so the comparisons below line up with the
        # cleaned names stored in the graph.
        person = self.find_person(person) or person

        # get the movies liked by this person
        persons_movies = self.get_liked_movies(person)
        
        # get the people who like any of these movies
        other_people = []
        for movie in persons_movies:
            this_movie_likers = self.get_movie_likers(movie)
            
            # only add if not already in the list
            for x in this_movie_likers:
                if x not in other_people:
                    other_people.append(x)
        
        
        # find out what movies these people like!
        movie_recs = []
        for other_person in other_people:
            their_movies = self.get_liked_movies(other_person)
            movie_recs = movie_recs + their_movies
        
        # take out the movies already watched
        movie_recs = [i for i in movie_recs if i not in persons_movies]
        
        
        # Count/Rank the movies
        top_recs = Counter(movie_recs).most_common(3)
        return top_recs
    
    def most_popular_movie(self):
        max_c = 0
        max_mov = ""
        prev = ""
        prev_c = 0
        for node in self.graph.graph.keys():
            if len(self.graph.graph[node]) > max_c:
                prev_c = max_c
                max_c = len(self.graph.graph[node])
                prev = max_mov
                max_mov = node
                

        return prev, prev_c

    def get_traversal_path(self, person):
        """Get the full traversal path for visualization"""
        person = self.find_person(person) or person
        path = {
            'person': person,
            'their_movies': [],
            'other_people': {},
            'recommended_movies': []
        }

        # Get their movies
        persons_movies = self.get_liked_movies(person)
        path['their_movies'] = persons_movies

        # For each movie, get who else liked it
        for movie in persons_movies:
            likers = self.get_movie_likers(movie)
            # Remove the person themselves
            other_likers = [p for p in likers if p != person]
            path['other_people'][movie] = other_likers

        # Get recommendations
        recs = self.recommend(person)
        path['recommended_movies'] = recs

        return path
            
            
def main():
    rec = Recommender()
    data = rec.read_csv("movies_data.csv")
    rec.add_to_graph(data)

    # What the cleaning bought us, in one line.
    stats = rec.cleaner.report()
    print(f"{stats['distinct_spellings']} spellings -> "
          f"{stats['distinct_movies']} movies "
          f"({len(stats['merged'])} titles had duplicates)")

    print(rec.recommend("Malika"))
    print(rec.most_popular_movie())
    print(rec.get_traversal_path("Abby"))
    
    
    
if __name__=='__main__':
    main()