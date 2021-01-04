import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table

from functions import dd_range_options, dd_options
from data import recipes_db, phdf_rec_ingr_tbl

BOOK_LIST = {
    'HH': 'HH Art of Eating Well',
    'GS': 'GS Good and Simple',
    'EG': 'EG Eat Green',
    'GG': 'GG Get the Glow',
    'LM': 'LM Custom Recipes',
    'BP': 'BP Custom Recipes'
}

UNITS_LIST = ['g', 'ml', 'medium', 'small', 'large', 'tbsp', 'tsp']

MTH_LIST = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
SEASONS_LIST = ['All', 'Spring', 'Summer', 'Autumn', 'Winter']

TAG_LIST = [
    'Indian',
    'Vegetarian',
    'Slow Cooked',
    'Cocotte-Friendly',
    'Entree',
    'Brunch',
    'Quick'
]

recipe_editor_layout = html.Div([
    # header row
    dbc.Row(
        dbc.Col([
            html.H3('Recipe Editor'),
            dcc.Dropdown(id='recipe_select', placeholder='Existing Recipe'),
            dcc.Input(id='r_name_input', placeholder='Recipe Name', autoComplete="off", size='200', type="text")
        ]), no_gutters=True),
    # recipe info row 1
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='r_book_select', placeholder='Book',
                         options=[{'label': name, 'value': code} for code, name in BOOK_LIST.items()]),
        ]),
        dbc.Col([
            dcc.Dropdown(id='r_page_select', placeholder='Page/Idx', options=dd_range_options(1,400)),
        ]),
        dbc.Col([
            dcc.Dropdown(id='r_servings_select', placeholder='Servings', options=dd_range_options(1, 8)),
        ]),
        dbc.Col([
            dcc.Dropdown(id='r_preptime_select', placeholder='Prep Time', options=dd_range_options(5,60,5)),
        ]),
        dbc.Col([
            dcc.Dropdown(id='r_cooktime_select', placeholder='Cook Time', options=dd_range_options(15,480,15)),
        ])
    ], no_gutters=True),
    # recipe info row 2
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='r_seasons_select', placeholder='Seasons',
                         options=[{'label': optn, 'value': optn} for optn in SEASONS_LIST
                                  ],
                         multi=False),
        ]),
        dbc.Col([
            dcc.Dropdown(id='r_months_select', placeholder='Months',
                         options=[{'label': optn, 'value': optn} for optn in MTH_LIST
                                  ],
                         multi=True),
        ]),
        dbc.Col([
            dcc.Dropdown(id='r_tag_select', placeholder='Tags',
                         options=[{'label': optn, 'value': optn} for optn in TAG_LIST
                                  ],
                         multi=True),
        ])
    ], no_gutters=True),
    # ingredients row
    dbc.Row([
        dbc.Col([
            html.Hr(),
            dcc.Dropdown(id='recipe_ingr_select', placeholder='Select Ingredients...',
                         options=dd_options('Ingredient', recipes_db), multi=True),
            html.Div([
                html.Br(),
                dash_table.DataTable(
                    id='recipe_ingr_table',
                    columns=[
                        {'id': p, 'name': p, 'presentation': 'dropdown', 'editable': True}
                        if p in {'Units', 'Sub Group'}
                        else ({'id': p, 'name': p, 'editable': True, 'type': 'numeric'}
                              if p in {'Quantity'}
                              else {'id': p, 'name': p})
                        for p in phdf_rec_ingr_tbl.columns
                    ],
                    editable=False,
                    dropdown={
                        'Units': {
                            'options': [
                                {'label': i, 'value': i}
                                for i in UNITS_LIST
                            ]
                        },
                        'Sub Group': {
                            'options': [{'label': str(i), 'value': i} for i in range(0, 5)]
                        }
                    },
                    data=phdf_rec_ingr_tbl.to_dict('records'),
                )
            ])
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.Br(),
            dbc.Button("Save", id='save_recipe_btn', block=True),
            dbc.Alert("Recipe Saved!", id='rec_saved_alert', color="success", is_open=False, duration=3000)
        ])
    ])

])

