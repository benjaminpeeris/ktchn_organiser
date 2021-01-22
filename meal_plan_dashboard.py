import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output

mp_dashboard_layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H3('Meal Planning Dashboard'),
            html.Div('Under Construction')
        ])
    ]),
    dbc.Row([dbc.Col([html.Div('Meh', id='meal_chart')])])
])
