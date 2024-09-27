import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
from flask import Flask

# Load data
data_path = r'Overall_Averages.xlsx'
df = pd.read_excel(data_path)

# Define maximum scores
max_scores = {
    "EST I total": 1600, "EST I - Literacy": 800, "EST I - Mathematics": 800,
    "EST I - Essay": 8, "EST II - Biology": 80, "EST II - Physics": 75,
    "EST II - Chemistry": 85, "EST II - Math 1": 50, "EST II - Math 2": 50,
    "EST II - Literature": 60, "EST II - World History": 65, "EST II - Economics": 60
}

# Initialize Flask app
server = Flask(__name__)

# Initialize Dash app
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.SPACELAB])

# App layout
app.layout = dbc.Container([
    dbc.Row([dbc.Col(html.H1("Student Performance Dashboard", className='text-center mb-4'), width=12)]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='student-search', 
            options=[{'label': user, 'value': user} for user in df['Username'].unique()],
            placeholder='Search for a student', className='mb-4'), width=6),
        dbc.Col(dcc.Dropdown(
            id='test-dropdown', 
            options=[{'label': test, 'value': test} for test in df['Test'].unique()],
            multi=True, placeholder='Select Test(s)', className='mb-4'), width=6),
        dbc.Col(dcc.Dropdown(
            id='country-dropdown', 
            options=[{'label': country, 'value': country} for country in df['Country'].unique()],
            multi=True, placeholder='Select Country', className='mb-4'), width=6),
        dbc.Col(dcc.Dropdown(
            id='test-version-dropdown',
            options=[{'label': 'Select All Versions', 'value': 'ALL'}] + 
                    [{'label': ver, 'value': ver} for ver in df['Version'].unique()],
            placeholder='Select Test Version', multi=True, className='mb-4'), width=6),
    ], className='mb-4'),
    dbc.Row([dbc.Col(html.Div(id='gauges-container', className='d-flex flex-wrap justify-content-center'))]),
    dbc.Row([dbc.Col(html.Div(id='totals-container', className='text-center mt-5'))])
], fluid=True, style={'max-width': '1100px', 'margin': '0 auto'})

# Helper function for wrapping text
def wrap_text(text, max_length=35):
    text = text.replace('A-SK-', '').replace('B-SK-', '').replace('C-SK-', '').replace('D-SK-', '')
    words, lines, line = text.split(), [], ""
    for word in words:
        if len(line) + len(word) + 1 <= max_length:
            line += (" " if line else "") + word
        else:
            lines.append(line)
            line = word
    if line: lines.append(line)
    return '<br>'.join(lines)

# Function to create gauge sections by test
def create_gauge_sections(filtered_df):
    sections = []
    for test in filtered_df['Test'].unique():
        skill_gauges = []
        for skill in filtered_df[filtered_df['Test'] == test]['Skill/Passage'].unique():
            row = filtered_df[(filtered_df['Test'] == test) & (filtered_df['Skill/Passage'] == skill)].iloc[0]
            avg_score, perc_score = row['Average Score'], row['Average Score'] * 100
            gauge = dcc.Graph(
                id=f'gauge-{skill}',
                figure=go.Figure(go.Indicator(
                    mode='gauge+number', value=perc_score,
                    title={'text': wrap_text(skill), 'font': {'size': 12}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': 'blue'}}
                )),
                style={'display': 'inline-block', 'width': '250px', 'height': '250px', 'margin': '10px'}
            )
            skill_gauges.append(dbc.Col(gauge, width=3))

        sections.append(dbc.Row([
            dbc.Col(html.H3(test, className='text-center my-4'), width=12),
            dbc.Col(dbc.Row(skill_gauges, className='d-flex justify-content-center'), width=12),
        ], className='mb-4', style={'border': '1px solid #dee2e6', 'padding': '15px', 'background-color': '#f8f9fa'}))
    return sections

# Function to calculate and display total sections
def create_totals_section(filtered_df):
    skill_totals, non_skill_totals = {}, {}
    for _, row in filtered_df.iterrows():
        skill, avg_score, perc_score = row['Skill/Passage'], row['Average Score'], row['Average Score'] * 100
        clean_title = skill.replace('A-SK-', '').replace('B-SK-', '').replace('C-SK-', '').replace('D-SK-', '')

        # Tally scores
        target_dict = skill_totals if '-SK-' in skill else non_skill_totals
        if clean_title in target_dict:
            target_dict[clean_title]['total_score'] += perc_score
            target_dict[clean_title]['count'] += 1
        else:
            target_dict[clean_title] = {'total_score': perc_score, 'count': 1}

    # Calculate averages and return sections
    avg_skill_scores = {title: data['total_score'] / data['count'] for title, data in skill_totals.items()}
    avg_non_skill_scores = {title: data['total_score'] / data['count'] for title, data in non_skill_totals.items()}
    skill_gauges, non_skill_gauges = [], []
    
    def generate_gauge(title, avg_score, color='blue'):
        return dcc.Graph(
            id=f'gauge-{title}-total',
            figure=go.Figure(go.Indicator(
                mode='gauge+number', value=avg_score,
                title={'text': wrap_text(title), 'font': {'size': 14}},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}}
            )),
            style={'display': 'inline-block', 'width': '320px', 'height': '320px'}
        )

    for title, avg_score in avg_skill_scores.items():
        skill_gauges.append(dbc.Col(generate_gauge(title, avg_score), width=3))
    for title, avg_score in avg_non_skill_scores.items():
        non_skill_gauges.append(dbc.Col(generate_gauge(title, avg_score), width=3))

    return dbc.Row(skill_gauges + non_skill_gauges, className='d-flex justify-content-center')

# Callback to update gauges and totals
@app.callback(
    [Output('gauges-container', 'children'), Output('totals-container', 'children')],
    [Input('student-search', 'value'), Input('test-dropdown', 'value'), Input('country-dropdown', 'value'),
     Input('test-version-dropdown', 'value')]
)
def update_gauges(student_search, selected_tests, selected_countries, test_versions):
    filtered_df = df.copy()
    if student_search: filtered_df = filtered_df[filtered_df['Username'] == student_search]
    if selected_tests: filtered_df = filtered_df[filtered_df['Test'].isin(selected_tests)]
    if selected_countries: filtered_df = filtered_df[filtered_df['Country'].isin(selected_countries)]
    if test_versions and 'ALL' not in test_versions: filtered_df = filtered_df[filtered_df['Version'].isin(test_versions)]

    gauge_sections = create_gauge_sections(filtered_df)
    total_sections = create_totals_section(filtered_df)

    return gauge_sections, total_sections

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
