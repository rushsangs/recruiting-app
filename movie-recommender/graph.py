#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  4 13:33:46 2025

@author: Rush Sanghrajka
DS2000 Section 3.
Graph
"""

class Graph:
    '''A graph is made up of nodes and edges.'''
    
    def __init__(self):
        ''' Create a new graph. New created graph is empty.'''
        # use an adjacency list. Dictionary where keys are nodes,
        # and the values are a list of neighbors for the node.
        self.graph = {}
    
    def __str__(self):
        '''This method gets called if someone tries to convert your
        object to str. Should return a string, which will get used whenever
        someone wants the string version of your object.'''
        # return "Graph with " + str(len(self.graph)) +  "nodes"
        return str(self.graph)
    
    def add_node(self, new_node):
        ''' Adds a node to the graph.'''
        # DON'T add node if already exists
        if new_node not in self.graph:
            # add an entry to the dictionary for the new node
            self.graph[new_node] = []

    def get_all_nodes(self):
        ''' Returns a list of all nodes in the graph.'''
        return list(self.graph.keys())

    def get_all_edges(self):
        ''' Returns a list of all edges in the graph.'''
        # loop through the graph and add all edges to a list
        edge_lst = []
        for node, neighbors in self.graph.items():
            for neighbor in neighbors:
                edge_lst.append((node, neighbor))
        return edge_lst

    def add_edge(self, node1, node2):
        ''' Adds an edge between two nodes.'''
        # if nodes don't exist, then create them before adding
        # an edge
        if node1 not in self.graph.keys():
            self.add_node(node1)
        if node2 not in self.graph.keys():
            self.add_node(node2)
        
        # if edge exists, then don't add it again.
        # add an edge for node 1, where node 2 is added to node1's list
        # of neighbors
        if node2 not in self.get_neighbors(node1):
            self.graph[node1].append(node2)
        
        # add an edge for node 2, where node 1 is added to node2's list
        # of neighbors
        if node1 not in self.get_neighbors(node2):
            self.graph[node2].append(node1)
    
    def get_neighbors(self, node):
        '''Returns a list of neighbors to the node.
        '''
        return self.graph.get(node, [])
        

