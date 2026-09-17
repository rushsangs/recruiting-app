# NU Recruiting — one-shot lecture

Two self-contained demos for the Northeastern recruiting lecture, plus the
slides (`slides.key` / `slides.pdf`). Each project has its own
`requirements.txt` and runs from its own directory.

## `cs-survey/` — live audience survey

A Streamlit app that collects five answers from the room, then visualizes them
live. The visualizations are built in deliberate good/bad pairs (an exploded 3D
pie next to a clean bar chart) to make the data-ink point on screen.

```bash
cd cs-survey
pip install -r requirements.txt
streamlit run app.py
```

Opens at <http://localhost:8501>. To let students reach it from their own
machines on the same network:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Responses append to `survey_responses.csv` **in the directory you launch
from** — so run it from inside `cs-survey/`, or the app will quietly start a
new empty file somewhere else.

## `movie-recommender/` — movie recommender

Students submit their top ten movies; the recommender builds a bipartite
people-to-movies graph and recommends from it. The same idea is implemented
twice on purpose, so the lecture can show a graph version and a plain-dictionary
version side by side.

```bash
cd movie-recommender
pip install -r requirements.txt
python dashboard.py
```

Opens at <http://localhost:5006> with three tabs: the bipartite graph, a
step-by-step recommendation walkthrough, and community clustering.

| File | What it is |
|------|------------|
| `graph.py` | Adjacency-list `Graph` class |
| `recommender.py` | Graph-based recommender; run it directly for a text demo |
| `dict_recommender.py` | The same idea with a co-occurrence dictionary |
| `clean.py` | Title cleaning — run it directly to see what it merges |
| `dashboard.py` | Panel + Plotly dashboard |
| `movies_data.csv` | 255 students |
| `movies_dataset.csv` | 63 students — what `dashboard.py` loads |

Each of these also runs on its own:

```bash
python recommender.py
```

```bash
python clean.py
```

### A note on the data

The survey responses are messy: the same film arrives as `Avengers: Endgame`,
`avengers endgame`, `Avengers End Game` and `Avenger's Endgame`. `clean.py`
groups those onto one matching key and picks the nicest spelling to display,
which takes 1282 distinct spellings down to about 1013 actual movies. Run it
directly to print the messiest titles in the data — it makes a good live demo
of why cleaning matters before any analysis.
