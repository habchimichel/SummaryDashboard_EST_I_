import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Load data
data_path = r'Overall_Averages.xlsx'
df = pd.read_excel(data_path)

# Define maximum scores for the columns
max_scores = {
    "EST I total": 1600,
    "EST I - Literacy": 800,
    "EST I - Mathematics": 800,
    "EST I - Essay": 8,
    "EST II - Biology": 80,
    "EST II - Physics": 75,
    "EST II - Chemistry": 85,
    "EST II - Math 1": 50,
    "EST II - Math 2": 50,
    "EST II - Literature": 60,
    "EST II - World History": 65,
    "EST II - Economics": 60
}

# App layout
st.title("Student Performance Dashboard")

# Dropdowns for user input
student_search = st.selectbox(
    'Search for a student by username',
    options=df['Username'].unique()
)

selected_versions = st.multiselect(
    'Select Test(s)',
    options=df['Test'].unique()
)

selected_countries = st.multiselect(
    'Select country(ies)',
    options=df['Country'].unique()
)

test_version = st.multiselect(
    'Select test version(s)',
    options=['Select All Versions'] + df['Version'].unique().tolist()
)

# Function to wrap text at spaces
def wrap_text(text, max_length=35):
    text = text.replace('A-SK-', '').replace('B-SK-', '').replace('C-SK-', '').replace('D-SK-', '')
    text = text.replace('A-', '').replace('B-', '').replace('C-', '').replace('D-', '')

    words = text.split()
    lines = []
    line = ""

    for word in words:
        if len(line) + len(word) + 1 <= max_length:
            if line:
                line += " "
            line += word
        else:
            lines.append(line)
            line = word

    if line:
        lines.append(line)

    return '<br>'.join(lines)

# Function to create gauge sections by test
def create_gauge_sections(filtered_df):
    sections = []
    tests = filtered_df['Test'].unique()

    for test in tests:
        test_df = filtered_df[filtered_df['Test'] == test]
        gauges = []
        skills = test_df['Skill/Passage'].unique()

        for skill in skills:
            skill_row = test_df[test_df['Skill/Passage'] == skill].iloc[0]
            average_score = skill_row['Average Score']
            percentage_score = average_score * 100

            bar_color = 'blue'
            title = wrap_text(skill)

            gauge = go.Figure(go.Indicator(
                mode='gauge+number',
                value=percentage_score,
                number={'font': {'size': 20, 'color': bar_color}},
                title={
                    'text': title,
                    'font': {'size': 12 if len(title.split('<br>')) > 1 else 14}
                },
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': bar_color}
                }
            ))

            gauges.append(gauge)

        sections.append((test, gauges))

    return sections

# Function to create totals section with gauges
def create_totals_section(filtered_df):
    skill_totals = {}
    non_skill_totals = {}

    for _, row in filtered_df.iterrows():
        skill_passage = row['Skill/Passage']
        average_score = row['Average Score']
        percentage_score = average_score * 100

        clean_title = skill_passage.replace('A-SK-', '').replace('B-SK-', '').replace('C-SK-', '').replace('D-SK-', '') \
                                   .replace('A-', '').replace('B-', '').replace('C-', '').replace('D-', '')

        if '-SK-' in skill_passage:
            if clean_title in skill_totals:
                skill_totals[clean_title]['total_score'] += percentage_score
                skill_totals[clean_title]['count'] += 1
            else:
                skill_totals[clean_title] = {'total_score': percentage_score, 'count': 1}
        else:
            if clean_title in non_skill_totals:
                non_skill_totals[clean_title]['total_score'] += percentage_score
                non_skill_totals[clean_title]['count'] += 1
            else:
                non_skill_totals[clean_title] = {'total_score': percentage_score, 'count': 1}

    avg_skill_scores = {title: data['total_score'] / data['count'] for title, data in skill_totals.items()}
    avg_non_skill_scores = {title: data['total_score'] / data['count'] for title, data in non_skill_totals.items()}

    return avg_skill_scores, avg_non_skill_scores

# Update and display gauges and totals based on user input
if student_search:
    filtered_df = df[df['Username'] == student_search]

    if selected_versions:
        filtered_df = filtered_df[filtered_df['Test'].isin(selected_versions)]

    if selected_countries:
        filtered_df = filtered_df[filtered_df['Country'].isin(selected_countries)]

    if test_version and 'Select All Versions' not in test_version:
        filtered_df = filtered_df[filtered_df['Version'].isin(test_version)]

    # Create gauge sections
    gauge_sections = create_gauge_sections(filtered_df)
    for test, gauges in gauge_sections:
        st.subheader(test)
        for gauge in gauges:
            st.plotly_chart(gauge)

    # Create totals section as gauges
    avg_skill_scores, avg_non_skill_scores = create_totals_section(filtered_df)
    
    st.subheader("Skill Totals")
    cols = st.columns(4)  # Create 4 columns for layout
    for i, (title, score) in enumerate(avg_skill_scores.items()):
        with cols[i % 4]:  # Use modulo operator to cycle through columns
            gauge = go.Figure(go.Indicator(
                mode='gauge+number',
                value=score,
                number={'font': {'size': 20, 'color': 'blue'}},
                title={'text': wrap_text(title), 'font': {'size': 12}},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': 'blue'}
                }
            ))
            st.plotly_chart(gauge)

    st.subheader("Non-Skill Totals")
    cols = st.columns(4)  # Create 4 columns for layout
    for i, (title, score) in enumerate(avg_non_skill_scores.items()):
        with cols[i % 4]:  # Use modulo operator to cycle through columns
            gauge = go.Figure(go.Indicator(
                mode='gauge+number',
                value=score,
                number={'font': {'size': 20, 'color': 'blue'}},
                title={'text': wrap_text(title), 'font': {'size': 12}},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': 'blue'}
                }
            ))
            st.plotly_chart(gauge)
