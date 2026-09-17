"""
Panel Dashboard for Movie Recommender System
Interactive visualization with bipartite graph, traversal demo, and clustering
"""
import panel as pn
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from recommender import Recommender
import numpy as np
from collections import Counter

# Enable Panel extensions
pn.extension('plotly')

class MovieBuddyDashboard:

    def __init__(self, csv_file):
        """Initialize the dashboard with movie data"""
        self.rec = Recommender()
        data = self.rec.read_csv(csv_file)
        self.rec.add_to_graph(data)

        # Create NetworkX graph for visualization
        self.nx_graph = nx.Graph()

        # Add all nodes and edges
        for node in self.rec.graph.get_all_nodes():
            node_type = 'person' if node in self.rec.people else 'movie'
            self.nx_graph.add_node(node, node_type=node_type)

        for edge in self.rec.graph.get_all_edges():
            self.nx_graph.add_edge(edge[0], edge[1])

        # Create widgets
        self.person_selector = pn.widgets.Select(
            name='Select a Person',
            options=sorted(list(self.rec.people)),
            value=None  # Start blank - no default selection
        )

        # Bind the selector to update methods
        self.person_selector.param.watch(self.update_traversal, 'value')

    def create_bipartite_graph(self):
        """Create bipartite graph visualization"""
        # Separate people and movies
        people = [n for n in self.nx_graph.nodes() if self.nx_graph.nodes[n]['node_type'] == 'person']
        movies = [n for n in self.nx_graph.nodes() if self.nx_graph.nodes[n]['node_type'] == 'movie']

        # Create bipartite layout
        pos = {}

        # Position people on the left
        for i, person in enumerate(people):
            pos[person] = (0, i * 10)

        # Position movies on the right
        for i, movie in enumerate(movies):
            pos[movie] = (10, i * 2)

        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in self.nx_graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )

        # Create people node trace
        people_x = [pos[node][0] for node in people]
        people_y = [pos[node][1] for node in people]

        people_trace = go.Scatter(
            x=people_x, y=people_y,
            mode='markers+text',
            hoverinfo='text',
            text=[node for node in people],
            textposition='middle left',
            marker=dict(
                size=10,
                color='#2E86AB',
                line=dict(width=2, color='white')
            ),
            name='People',
            hovertext=[f"{node}<br>{len(self.rec.get_liked_movies(node))} movies" for node in people]
        )

        # Create movie node trace (smaller, no labels for readability)
        movies_x = [pos[node][0] for node in movies]
        movies_y = [pos[node][1] for node in movies]

        movies_trace = go.Scatter(
            x=movies_x, y=movies_y,
            mode='markers',
            hoverinfo='text',
            marker=dict(
                size=6,
                color='#A23B72',
                line=dict(width=1, color='white')
            ),
            name='Movies',
            hovertext=[f"{node}<br>{len(self.rec.get_movie_likers(node))} people" for node in movies]
        )

        # Create figure
        fig = go.Figure(data=[edge_trace, people_trace, movies_trace])

        fig.update_layout(
            title='Movie Buddy Bipartite Graph',
            title_font_size=20,
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=800,
            autosize=True,
            plot_bgcolor='white'
        )

        return pn.pane.Plotly(fig, sizing_mode='stretch_width')

    def create_traversal_visualization(self, person):
        """Create visualization showing the traversal path for recommendations"""
        if not person or person not in self.rec.people:
            return pn.pane.Markdown("## Select a person to see recommendations")

        # Get their movies first
        persons_movies = self.rec.get_liked_movies(person)
        if not persons_movies:
            return pn.pane.Markdown(f"## No Movies Found\n\n{person} hasn't listed any movies yet. They need to fill out the survey!")

        try:
            path = self.rec.get_traversal_path(person)

            # Create a smaller subgraph for this traversal
            G = nx.Graph()

            # Add the person
            G.add_node(person, node_type='person', layer=0)

            # Add their movies
            for movie in path['their_movies']:
                G.add_node(movie, node_type='movie', layer=1)
                G.add_edge(person, movie)

            # Add other people who liked those movies
            other_people_set = set()
            for movie in path['their_movies']:
                for other_person in path['other_people'].get(movie, []):
                    if other_person not in other_people_set:
                        G.add_node(other_person, node_type='person', layer=2)
                        other_people_set.add(other_person)
                    G.add_edge(movie, other_person)

            # Add recommended movies
            for movie, count in path['recommended_movies'][:5]:
                if movie not in G.nodes():
                    G.add_node(movie, node_type='rec_movie', layer=3)
                # Connect to people who liked it
                likers = self.rec.get_movie_likers(movie)
                for liker in likers:
                    if liker in G.nodes():
                        G.add_edge(movie, liker)

            # Create hierarchical layout
            pos = nx.multipartite_layout(G, subset_key='layer', scale=2)

            # Create edge traces
            edge_x = []
            edge_y = []
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=1, color='#888'),
                hoverinfo='none',
                mode='lines',
                showlegend=False
            )

            # Create node traces by type
            traces = []

            # Target person (highlighted)
            target_x = [pos[person][0]]
            target_y = [pos[person][1]]
            traces.append(go.Scatter(
                x=target_x, y=target_y,
                mode='markers+text',
                text=[person],
                textposition='top center',
                marker=dict(size=20, color='#E63946', line=dict(width=3, color='white')),
                name='You',
                hovertext=[f"{person}"]
            ))

            # Their movies
            their_movies_nodes = path['their_movies']
            if their_movies_nodes:
                mx = [pos[m][0] for m in their_movies_nodes if m in pos]
                my = [pos[m][1] for m in their_movies_nodes if m in pos]
                traces.append(go.Scatter(
                    x=mx, y=my,
                    mode='markers+text',
                    text=their_movies_nodes,
                    textposition='top center',
                    textfont=dict(size=8),
                    marker=dict(size=12, color='#A23B72'),
                    name='Your Movies',
                    hovertext=[f"{m}" for m in their_movies_nodes]
                ))

            # Other people
            if other_people_set:
                ox = [pos[p][0] for p in other_people_set if p in pos]
                oy = [pos[p][1] for p in other_people_set if p in pos]
                traces.append(go.Scatter(
                    x=ox, y=oy,
                    mode='markers',
                    marker=dict(size=10, color='#2E86AB'),
                    name='Similar People',
                    hovertext=[f"{p}" for p in other_people_set]
                ))

            # Recommended movies
            rec_movies = [m for m, c in path['recommended_movies'][:5]]
            if rec_movies:
                rx = [pos[m][0] for m in rec_movies if m in pos]
                ry = [pos[m][1] for m in rec_movies if m in pos]
                rec_labels = [f"{m}\n({c} connections)" for m, c in path['recommended_movies'][:5] if m in pos]
                traces.append(go.Scatter(
                    x=rx, y=ry,
                    mode='markers+text',
                    text=rec_labels,
                    textposition='top center',
                    textfont=dict(size=8),
                    marker=dict(size=15, color='#F77F00', line=dict(width=2, color='white')),
                    name='Recommended',
                    hovertext=rec_labels
                ))

            # Create figure
            fig = go.Figure(data=[edge_trace] + traces)

            fig.update_layout(
                title=f'How We Recommend Movies for {person}',
                title_font_size=18,
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=60),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=600,
                autosize=True,
                plot_bgcolor='white'
            )

            # Create recommendations table
            rec_text = f"### Recommendations for {person}\n\n"
            if path['recommended_movies']:
                rec_text += "| Movie | Connections |\n|-------|-------------|\n"
                for movie, count in path['recommended_movies'][:5]:
                    # Names come out of the graph already cleaned, so don't
                    # run .title() over them -- it would turn "Spy x Family"
                    # into "Spy X Family".
                    rec_text += f"| {movie} | {count} |\n"
            else:
                rec_text += "*No recommendations available*"

            return pn.Column(
                pn.pane.Plotly(fig, sizing_mode='stretch_width'),
                pn.pane.Markdown(rec_text)
            )
        except Exception as e:
            return pn.pane.Markdown(f"## Visualization Error\n\n{person} exists but couldn't create visualization: {str(e)}\n\nThis might happen if they have no movie connections.")

    def community_layout(self, subgraph, communities, pull=0.20):
        """Lay out the graph so each community is its own visible blob.

        A plain spring_layout over the whole graph produces a hairball: the
        popular movies are connected to everybody, so they drag every
        community into the middle and the clusters overlap into one mass.

        The fix is to lay it out twice, at two different scales:
          1. Collapse each community to a single point and lay *those* out,
             so communities that share a lot of edges land near each other.
          2. Lay out each community internally, on its own, then shrink it
             and drop it onto its point from step 1.

        Because step 2 only ever sees one community's own edges, the hub
        movies can't pull the clusters together any more.
        """
        # Step 1: the "meta graph" -- one node per community, edge weights
        # counting how many edges run between each pair of communities.
        member_of = {}
        for index, community in enumerate(communities):
            for node in community:
                member_of[node] = index

        meta = nx.Graph()
        meta.add_nodes_from(range(len(communities)))
        for node_a, node_b in subgraph.edges():
            home_a, home_b = member_of[node_a], member_of[node_b]
            if home_a != home_b:
                weight = meta.get_edge_data(home_a, home_b, {}).get('weight', 0)
                meta.add_edge(home_a, home_b, weight=weight + 1)

        # Spread the community centres out. k is large so they sit well apart.
        centres = nx.spring_layout(meta, k=2.5, iterations=200, seed=42,
                                   weight='weight')

        # Step 2: lay out each community on its own and place it at its centre.
        pos = {}
        for index, community in enumerate(communities):
            members = list(community)
            inner = self.nx_graph.subgraph(members)
            local = nx.spring_layout(inner, k=0.9, iterations=100, seed=42)

            # Bigger communities need more room, but scale by sqrt so a
            # 60-node community doesn't swamp a 5-node one.
            radius = pull * (len(members) ** 0.5)
            centre_x, centre_y = centres[index]
            for node in members:
                pos[node] = (centre_x + local[node][0] * radius,
                             centre_y + local[node][1] * radius)

        return pos

    def create_cluster_view(self):
        """Create community detection visualization"""
        # Use community detection
        all_communities = nx.community.greedy_modularity_communities(self.nx_graph)

        # Filter out single-node communities, biggest first so the colours
        # go to the communities worth talking about.
        communities = sorted((c for c in all_communities if len(c) > 1),
                             key=len, reverse=True)

        nodes_to_plot = set()
        for community in communities:
            nodes_to_plot.update(community)
        subgraph = self.nx_graph.subgraph(nodes_to_plot)

        # Position the nodes cluster by cluster instead of all at once.
        pos = self.community_layout(subgraph, communities)

        # Six hues that stay distinguishable for colourblind viewers even
        # when every pair is on screen at once (checked with the palette
        # validator). There is no seventh colour: cycling the palette would
        # give communities 1 and 7 the same colour and make the legend lie,
        # so everything past the top six is grey "Other".
        colors = ['#2a78d6', '#1baf7a', '#eda100', '#008300', '#4a3aa7', '#e34948']
        OTHER_COLOR = '#8a8a86'
        named_count = min(len(communities), len(colors))

        community_map = {}
        for index, community in enumerate(communities):
            for node in community:
                community_map[node] = index

        # Draw the edges in two passes. Edges inside a cluster are what make
        # it a cluster, so they stay visible; edges between clusters are
        # drawn very faint, or they fill the gaps back in.
        inside_x, inside_y, between_x, between_y = [], [], [], []
        for node_a, node_b in subgraph.edges():
            x0, y0 = pos[node_a]
            x1, y1 = pos[node_b]
            same_cluster = community_map[node_a] == community_map[node_b]
            target_x = inside_x if same_cluster else between_x
            target_y = inside_y if same_cluster else between_y
            target_x.extend([x0, x1, None])
            target_y.extend([y0, y1, None])

        traces = [
            go.Scatter(x=between_x, y=between_y, mode='lines',
                       line=dict(width=0.3, color='#e2e2df'),
                       hoverinfo='none', showlegend=False),
            go.Scatter(x=inside_x, y=inside_y, mode='lines',
                       line=dict(width=0.6, color='#b8b8b3'),
                       hoverinfo='none', showlegend=False),
        ]

        # One trace per community, plus one for everything folded into Other.
        other_nodes = []

        for index, community in enumerate(communities):
            members = sorted(community)
            if index >= named_count:
                other_nodes.extend(members)
                continue

            # People and movies get different shapes, so the clusters are
            # still readable if the colours are hard to tell apart.
            symbols = ['circle' if node in self.rec.people else 'diamond'
                       for node in members]
            sizes = [9 if node in self.rec.people else 7 for node in members]
            labels = [
                f"{node}<br>{'Person' if node in self.rec.people else 'Movie'}"
                f" · Community {index + 1}"
                for node in members
            ]

            traces.append(go.Scatter(
                x=[pos[node][0] for node in members],
                y=[pos[node][1] for node in members],
                mode='markers',
                hoverinfo='text',
                marker=dict(size=sizes, symbol=symbols, color=colors[index],
                            line=dict(width=1, color='white')),
                name=f"{index + 1}. {self.describe_community(community)}",
                hovertext=labels
            ))

        if other_nodes:
            traces.append(go.Scatter(
                x=[pos[node][0] for node in other_nodes],
                y=[pos[node][1] for node in other_nodes],
                mode='markers',
                hoverinfo='text',
                marker=dict(size=6, symbol='circle', color=OTHER_COLOR,
                            line=dict(width=1, color='white')),
                name=f'Other ({len(communities) - named_count} small groups)',
                hovertext=other_nodes
            ))

        fig = go.Figure(data=traces)

        fig.update_layout(
            title='Movie Taste Communities (Netflix-style Clustering)',
            title_font_size=18,
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=60),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            # Lock the aspect ratio so the clusters read as round blobs
            # instead of being smeared into one wide ellipse.
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       scaleanchor='x', scaleratio=1),
            height=700,
            autosize=True,
            plot_bgcolor='white',
            legend=dict(font=dict(size=11), itemsizing='constant')
        )

        cluster_text = f"### Found {len(communities)} Movie Taste Communities (groups of 2+)\n\n"
        cluster_text += ("Each blob is a group of people and movies that are closely connected. "
                         "Circles are people, diamonds are movies. Netflix uses similar "
                         "clustering (but with thousands of variables!) to group users and content.\n\n")

        # Spell the clusters out in a table too -- easier to read off a
        # projector than the colours, and it names what each group is about.
        cluster_text += "| # | Community | People | Movies | Typical movies |\n"
        cluster_text += "|---|-----------|--------|--------|----------------|\n"
        for index, community in enumerate(communities[:named_count]):
            people = [n for n in community if n in self.rec.people]
            movies = [n for n in community if n not in self.rec.people]
            top_movies = sorted(movies, key=lambda m: self.nx_graph.degree(m),
                                reverse=True)[:3]
            cluster_text += (f"| {index + 1} | {self.describe_community(community)} "
                             f"| {len(people)} | {len(movies)} "
                             f"| {', '.join(top_movies) if top_movies else '--'} |\n")

        return pn.Column(
            pn.pane.Plotly(fig, sizing_mode='stretch_width'),
            pn.pane.Markdown(cluster_text)
        )

    def describe_community(self, community):
        """Name a community after its most-connected movie.

        "Community 4" tells you nothing. "Interstellar crowd" tells you what
        the cluster is actually about, which is the whole point of showing it.
        """
        movies = [n for n in community if n not in self.rec.people]
        if not movies:
            return f'{len(community)} people'
        top_movie = max(movies, key=lambda m: self.nx_graph.degree(m))
        return f'{top_movie} crowd ({len(community)})'

    def update_traversal(self, event):
        """Update traversal visualization when person is selected"""
        try:
            person = event.new
            new_viz = self.create_traversal_visualization(person)
            self.traversal_pane.objects = [new_viz]
        except Exception as e:
            error_msg = pn.pane.Markdown(f"## Error\n\nCould not create visualization for {person}: {str(e)}")
            self.traversal_pane.objects = [error_msg]

    def create_dashboard(self):
        """Create the full dashboard"""
        # Create tabs for different views
        bipartite_tab = pn.Column(
            pn.pane.Markdown("## Bipartite Graph: People ↔ Movies"),
            pn.pane.Markdown("People are on the left (blue), movies on the right (purple). "
                           "Hover over nodes to see details."),
            self.create_bipartite_graph()
        )

        # Initialize traversal pane as a Row that we can update
        initial_person = self.person_selector.value
        if initial_person:
            initial_viz = self.create_traversal_visualization(initial_person)
        else:
            initial_viz = pn.pane.Markdown("## Select a person to see recommendations")
        self.traversal_pane = pn.Row(initial_viz)

        traversal_tab = pn.Column(
            pn.pane.Markdown("## Live Recommendation Demo"),
            pn.pane.Markdown("Select a person to see how we traverse the graph to find recommendations:"),
            self.person_selector,
            self.traversal_pane
        )

        cluster_tab = pn.Column(
            pn.pane.Markdown("## How Netflix Does It"),
            pn.pane.Markdown("This shows communities (clusters) of similar movie taste. "
                           "Netflix uses this approach with thousands of variables!"),
            self.create_cluster_view()
        )

        tabs = pn.Tabs(
            ('📊 Bipartite Graph', bipartite_tab),
            ('🎯 Recommendation Demo', traversal_tab),
            ('🎬 Clusters (Netflix Style)', cluster_tab)
        )

        dashboard = pn.Column(
            pn.pane.Markdown("# 🎬 From Numbers to Stories: Finding Your Movie Buddy"),
            pn.pane.Markdown("*Interactive visualization of our movie recommendation system*"),
            tabs,
            sizing_mode='stretch_width'
        )

        return dashboard

# Main execution
if __name__ == '__main__':
    # Create dashboard
    dashboard = MovieBuddyDashboard('movies_dataset.csv')
    app = dashboard.create_dashboard()

    # Serve the dashboard
    pn.serve(app, port=5006, show=True, title="Movie Buddy Dashboard")