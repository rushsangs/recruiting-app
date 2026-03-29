import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# File to store responses
RESPONSES_FILE = "survey_responses.csv"

# Initialize session state
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'form'

# Survey questions
QUESTIONS = {
    'q1': {
        'question': 'What draws you most to studying computer science?',
        'type': 'select',
        'options': [
            'Building things that matter',
            'Solving complex problems',
            'High-paying career opportunities',
            'Creating games or apps',
            'Using AI/ML to change the world',
            'Making technology more accessible'
        ]
    },
    'q2': {
        'question': 'How many programming languages have you used (even just a little)?',
        'type': 'number',
        'min': 0,
        'max': 10
    },
    'q3': {
        'question': 'Which CS area interests you most right now?',
        'type': 'select',
        'options': [
            'Artificial Intelligence',
            'Cybersecurity',
            'Game Development',
            'Web/App Development',
            'Data Science',
            'Robotics',
            'Not sure yet'
        ]
    },
    'q4': {
        'question': 'How many hours per week do you spend on screens for fun (not school)?',
        'type': 'number',
        'min': 0,
        'max': 100
    },
    'q5': {
        'question': 'What excites you most about college?',
        'type': 'select',
        'options': [
            'Learning from expert professors',
            'Working on real-world projects',
            'Meeting people from diverse backgrounds',
            'Independence and freedom',
            'Co-op/internship opportunities',
            'Being in Boston'
        ]
    }
}


def save_response(responses):
    """Save survey response to CSV"""
    df = pd.DataFrame([responses])
    df['timestamp'] = datetime.now()

    if os.path.exists(RESPONSES_FILE):
        existing_df = pd.read_csv(RESPONSES_FILE)
        df = pd.concat([existing_df, df], ignore_index=True)

    df.to_csv(RESPONSES_FILE, index=False)


def load_responses():
    """Load all survey responses"""
    if os.path.exists(RESPONSES_FILE):
        return pd.read_csv(RESPONSES_FILE)
    return pd.DataFrame()


def create_viz_motivation(df):
    """Visualization 1: What draws students to CS - demonstrate good vs bad viz"""
    st.subheader("What Draws You to Computer Science?")

    col1, col2 = st.columns(2)

    with col1:
        st.caption("❌ 3D Pie Chart (Hard to read, chart junk)")
        # Create a 3D-ish pie chart (purposely bad)
        fig_bad = go.Figure(data=[go.Pie(
            labels=df['q1'].value_counts().index,
            values=df['q1'].value_counts().values,
            hole=0.3,
            pull=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
            marker=dict(colors=px.colors.qualitative.Bold)
        )])
        fig_bad.update_layout(
            height=300,
            scene=dict(camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_bad, use_container_width=True)

    with col2:
        st.caption("✅ Simple Bar Chart (Clear, honest)")
        # Create a clean bar chart
        counts = df['q1'].value_counts().sort_values(ascending=True)
        fig_good = px.bar(
            x=counts.values,
            y=counts.index,
            orientation='h',
            labels={'x': 'Number of Students', 'y': ''},
            color=counts.values,
            color_continuous_scale='Blues'
        )
        fig_good.update_layout(
            height=300,
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        fig_good.update_coloraxes(showscale=False)
        st.plotly_chart(fig_good, use_container_width=True)

    st.markdown("**Tufte Principle**: Maximize data-ink ratio. Remove chart junk.")


def create_viz_experience(df):
    """Visualization 2: Programming experience distribution"""
    st.subheader("Programming Experience: What Does the Distribution Tell Us?")

    # Create histogram with annotations
    fig = px.histogram(
        df,
        x='q2',
        nbins=11,
        labels={'q2': 'Number of Languages Used', 'count': 'Number of Students'},
        title='',
        color_discrete_sequence=['#2E86AB']
    )

    # Add mean line
    mean_val = df['q2'].mean()
    fig.add_vline(x=mean_val, line_dash="dash", line_color="red",
                  annotation_text=f"Average: {mean_val:.1f}",
                  annotation_position="top")

    fig.update_layout(
        height=400,
        showlegend=False,
        bargap=0.1
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Median", f"{df['q2'].median():.0f} languages")
    col2.metric("Most Common", f"{df['q2'].mode().values[0]:.0f} languages")
    col3.metric("Range", f"{df['q2'].min():.0f}-{df['q2'].max():.0f}")

    st.markdown("**Story**: The distribution reveals experience diversity in our community.")


def create_viz_interests(df):
    """Visualization 3: CS interests - categorical comparison"""
    st.subheader("Where Your Interests Lie")

    # Count and sort
    interest_counts = df['q3'].value_counts()

    # Create a lollipop chart (more interesting than bar)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=interest_counts.values,
        y=interest_counts.index,
        mode='markers',
        marker=dict(
            size=20,
            color=interest_counts.values,
            colorscale='Viridis',
            showscale=False,
            line=dict(width=2, color='white')
        ),
        name=''
    ))

    # Add lines
    for i, (idx, val) in enumerate(interest_counts.items()):
        fig.add_trace(go.Scatter(
            x=[0, val],
            y=[idx, idx],
            mode='lines',
            line=dict(color='lightgray', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))

    fig.update_layout(
        xaxis_title='Number of Students',
        yaxis_title='',
        height=400,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Design Choice**: Lollipop chart draws attention to individual values while maintaining comparison.")


def create_viz_screen_time(df):
    """Visualization 4: Screen time - show distribution with context"""
    st.subheader("Screen Time Reality Check")

    # Create box plot with individual points
    fig = go.Figure()

    fig.add_trace(go.Box(
        y=df['q4'],
        name='',
        boxmean='sd',
        marker_color='#A23B72',
        fillcolor='rgba(162, 59, 114, 0.3)'
    ))

    fig.add_trace(go.Scatter(
        y=df['q4'],
        x=[0] * len(df),
        mode='markers',
        marker=dict(size=8, color='rgba(162, 59, 114, 0.6)'),
        name='Individual responses',
        showlegend=False
    ))

    fig.update_layout(
        yaxis_title='Hours per Week',
        height=400,
        showlegend=False,
        margin=dict(t=20, b=40, l=60, r=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Context
    avg = df['q4'].mean()
    st.info(f"📊 Average: {avg:.1f} hours/week = {avg / 7:.1f} hours/day")
    st.markdown("**Principle**: Show the data in context. What does this number *mean*?")


def create_viz_excitement(df):
    """Visualization 5: College excitement - tell a story"""
    st.subheader("What Excites You About College?")

    excitement_counts = df['q5'].value_counts()

    # Create a radial/polar bar chart for variety
    fig = go.Figure(go.Barpolar(
        r=excitement_counts.values,
        theta=excitement_counts.index,
        marker_color=px.colors.sequential.Plasma_r,
        marker_line_color="white",
        marker_line_width=2,
        opacity=0.8
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(showticklabels=True, ticks=''),
            angularaxis=dict(direction='clockwise')
        ),
        height=500,
        margin=dict(t=40, b=40, l=80, r=80)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "**Design Choice**: Different visualizations for different narratives. This shows no single answer dominates—you're all here for different reasons.")


# Main app
st.set_page_config(page_title="Welcome Day Survey", layout="wide")

# Mode selector in sidebar (hidden from students)
with st.sidebar:
    st.title("Mode")
    if st.button("📝 Survey Form"):
        st.session_state.view_mode = 'form'
    if st.button("📊 Dashboard"):
        st.session_state.view_mode = 'dashboard'

    st.divider()

    # Show response count
    df = load_responses()
    if not df.empty:
        st.metric("Total Responses", len(df))

    # Clear data option
    if st.button("🗑️ Clear All Data"):
        if os.path.exists(RESPONSES_FILE):
            os.remove(RESPONSES_FILE)
            st.success("Data cleared!")
            st.rerun()

# FORM VIEW
if st.session_state.view_mode == 'form':
    st.title("🎓 Welcome to Khoury College!")
    st.markdown("### Help us learn about you")
    st.markdown("Your responses are anonymous and will be used in today's demonstration.")

    with st.form("survey_form"):
        responses = {}

        # Question 1
        responses['q1'] = st.selectbox(
            QUESTIONS['q1']['question'],
            options=QUESTIONS['q1']['options'],
            index=None,
            placeholder="Choose one..."
        )

        # Question 2
        responses['q2'] = st.number_input(
            QUESTIONS['q2']['question'],
            min_value=QUESTIONS['q2']['min'],
            max_value=QUESTIONS['q2']['max'],
            value=0,
            step=1
        )

        # Question 3
        responses['q3'] = st.selectbox(
            QUESTIONS['q3']['question'],
            options=QUESTIONS['q3']['options'],
            index=None,
            placeholder="Choose one..."
        )

        # Question 4
        responses['q4'] = st.number_input(
            QUESTIONS['q4']['question'],
            min_value=QUESTIONS['q4']['min'],
            max_value=QUESTIONS['q4']['max'],
            value=0,
            step=1
        )

        # Question 5
        responses['q5'] = st.selectbox(
            QUESTIONS['q5']['question'],
            options=QUESTIONS['q5']['options'],
            index=None,
            placeholder="Choose one..."
        )

        submitted = st.form_submit_button("Submit", type="primary", use_container_width=True)

        if submitted:
            # Validate
            if responses['q1'] is None or responses['q3'] is None or responses['q5'] is None:
                st.error("Please answer all questions!")
            else:
                save_response(responses)
                st.success("✅ Thank you! Your response has been recorded.")
                st.balloons()

# DASHBOARD VIEW
else:
    st.title("From Numbers to Stories")
    st.markdown("### Live Data Science with Your Responses")

    df = load_responses()

    if df.empty:
        st.info("No responses yet. Have students submit the survey first!")
    else:
        st.success(f"**{len(df)} responses collected**")

        st.divider()

        # Create all visualizations
        create_viz_motivation(df)
        st.divider()

        create_viz_experience(df)
        st.divider()

        create_viz_interests(df)
        st.divider()

        create_viz_screen_time(df)
        st.divider()

        create_viz_excitement(df)

        st.divider()
        st.markdown("### 🎯 Key Takeaways")
        st.markdown("""
        - **Good visualization tells a story** - it doesn't just show data
        - **Remove chart junk** - every element should serve the data
        - **Choose the right visualization for your message** - bars vs. boxes vs. radial
        - **Context matters** - 40 hours means something different than just '40'
        - **Honest representation** - your choices can reveal or obscure truth
        """)