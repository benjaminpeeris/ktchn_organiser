import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table

from dash.dependencies import Input, Output

from data import recipes_db, day_map, phdf_shopping_list, TAG_LIST, MTH_LIST, phdf_meal_summary, recipes_full
from functions import dd_options, get_startdate, dynamic_filter

meal_plan_tbl_hdr = [
    html.Thead(html.Tr([
        html.Th(dbc.Alert("Day", color="secondary")),
        html.Th(dbc.Alert("Lunch (L)", color="info")),
        html.Th(dbc.Alert("Lunch (B)", color="warning")),
        html.Th(dbc.Alert("Dinner (L)", color="info")),
        html.Th(dbc.Alert("Dinner (B)", color="warning"))
    ]))
]

calrow = {}

for day in ['sat', 'sun', 'mon', 'tue', 'wed', 'thu', 'fri']:
    calrow[day] = html.Tr([
        html.Td(html.Label(day_map[day])),
        html.Td(dcc.Dropdown(id=day + '_ll')),
        html.Td(dcc.Dropdown(id=day + '_lb')),
        html.Td(dcc.Dropdown(id=day + '_dl')),
        html.Td(dcc.Dropdown(id=day + '_db'))
    ])

# meal_plan_tbl_body = [html.Tbody([calrow['sat']])]
meal_plan_tbl_body = [html.Tbody([v for v in calrow.values()])]

meal_planner_layout = html.Div([
    dbc.Row(
        dbc.Col([
            html.H3('Meal Plan'),
            html.Div('For week starting on Saturday, '),
            dcc.Dropdown(
                id='week_select',
                options=[{'label': i, 'value': i} for i in [get_startdate(j, fmt_as_code=True) for j in range(-3, 4)]],
                value=get_startdate(0, fmt_as_code=True),
                clearable=False
            ),
            html.Hr(),
            html.Label("Select meals for this week"),
        ])),
    # meals selection
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='ingr_filter', options=dd_options('Ingredient', recipes_db()),
                         multi=True, placeholder='Recipe Ingredient(s)')
        ]),
        dbc.Col([
            dcc.Dropdown(id='month_filter', options=[{'label': optn, 'value': optn} for optn in MTH_LIST],
                         multi=True, placeholder='Month(s)')
        ]),
        dbc.Col([
            dcc.Dropdown(id='tag_filter', options=[{'label': optn, 'value': optn} for optn in TAG_LIST],
                         multi=True, placeholder='Tag(s)')
        ]),
        dbc.Col([
            dbc.Button("Import", id='gsheet_import_btn', block=True, color="primary")
        ])
    ], no_gutters=True),
    dbc.Row(
        dbc.Col([
            dcc.Dropdown(
                id='recipe_select',
                options=dd_options('Recipe', recipes_db()),
                multi=True
            ),
            html.Div(id='cook_time_chart_div')
        ])),
    # meal plan table
    html.H6('Detailed Meal Plan'),
    dbc.Table(meal_plan_tbl_hdr + meal_plan_tbl_body, bordered=False),
    html.Hr(),
    dbc.Textarea(id="add_remarks", placeholder="Add notes for the meal plan..."),
    html.Hr(),
    html.H6('Weekly Meal Summary'),
    dbc.Row(dbc.Col([
        dash_table.DataTable(
            id='meal_week_summary_table',
            columns=(
                [{'id': p, 'name': p, 'type': 'numeric', 'editable': p in ['Supplementary Meals']}
                 for p in phdf_meal_summary.columns]
            ),
            data=phdf_meal_summary.to_dict('records'),
        ),
        dbc.Button("Generate Shopping List", id='shopping_list_gen_btn', block=True, color="primary")
    ])),
    html.Hr(),
    # manual save button
    dbc.Button("Manual Save", id='manual_save_button', block=True, color="primary"),
    html.Hr(),
    # shopping list table

    dbc.Row(dbc.Col([
        dash_table.DataTable(
                id='shopping_list_table',
                columns=(
                    [{'id': p, 'name': p, 'type': 'numeric'} for p in phdf_shopping_list.columns]
                ),
                data=phdf_shopping_list.to_dict('records'),
                sort_action='native',
                editable=False,
                row_deletable=True,
            ),
        html.Br(),
        dbc.Button("Copy Shopping List", id='shopping_list_copy_btn', block=True, color="primary"),
        dbc.Alert("Shopping List Copied!", id='copied_alert', color="success", is_open=False, duration=3000)

    ]))

])



