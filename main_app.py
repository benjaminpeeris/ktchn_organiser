import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output, State
import os
import datetime as dt
import plotly.express as px

from meal_planner import meal_planner_layout
from recipe_editor import recipe_editor_layout
from meal_plan_dashboard import mp_dashboard_layout
from data import recipes_db, recipes_full, phdf_rec_ingr_tbl, ingredients_db, meal_plan, season_map
from functions import get_rec_id, valid_rec, dd_options, dynamic_filter, dash_context, get_recipe_info

NO_OF_PERSONS = 2
REQD_FILL_PCT = 1  # all required to be filled for saving

EXCL_REC = {'Eat Out', 'Dummy1', 'Dummy2'}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config['suppress_callback_exceptions'] = True
app.title = 'Meal Planner'

app.layout = html.Div([
    # tab_row, default to planning_view (tab-1)
    dcc.Tabs(id='tab_row', value='tab-1', children=[
        dcc.Tab(label='Planning View', value='tab-1'),
        dcc.Tab(label='Recipe View', value='tab-2'),
        dcc.Tab(label='Dashboard View', value='tab-3'),

    ]),
    html.Br(),
    # content row
    html.Div(id='tab-content')
])

@app.callback(Output('tab-content', 'children'),
              Input('tab_row', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return meal_planner_layout
    elif tab == 'tab-2':
        return recipe_editor_layout
    elif tab == 'tab-3':
        return mp_dashboard_layout


# ------ MEAL PLANNER -------!
@app.callback(Output('recipe_select', 'options'),
              [Input('ingr_filter', 'value'),
               Input('month_filter', 'value'),
               Input('tag_filter', 'value')])
def update_options(ingr_list, mth_list, tag_list):
    df = recipes_full()
    print("filters", ingr_list, mth_list, tag_list)
    df_filtered = dynamic_filter(df, Ingredient=ingr_list, Months=mth_list, Tags=tag_list)
    return dd_options('Recipe', df_filtered)


@app.callback(Output('recipe_select', 'value'),
              Output('sat_ll','value'), Output('sat_lb','value'),
              Output('sat_dl','value'), Output('sat_db','value'),
              Output('sun_ll','value'), Output('sun_lb','value'),
              Output('sun_dl','value'), Output('sun_db','value'),
              Output('mon_ll','value'), Output('mon_lb','value'),
              Output('mon_dl','value'), Output('mon_db','value'),
              Output('tue_ll','value'), Output('tue_lb','value'),
              Output('tue_dl','value'), Output('tue_db','value'),
              Output('wed_ll','value'), Output('wed_lb','value'),
              Output('wed_dl','value'), Output('wed_db','value'),
              Output('thu_ll','value'), Output('thu_lb','value'),
              Output('thu_dl','value'), Output('thu_db','value'),
              Output('fri_ll','value'), Output('fri_lb','value'),
              Output('fri_dl','value'), Output('fri_db','value'),
              Input('week_select', 'value'))
def update_existing_recipe(weekdate):
    df = meal_plan(weekdate)
    if df.shape[0] == 0:
        print("No data found for", weekdate)
        return [], None, None, None, None, None, None, None, None, \
               None, None, None, None, None, None, None, None, \
               None, None, None, None, None, None, None, None, None, None, None, None
    else:
        print("Data found for", weekdate)
        r_list = [i for i in df['Recipe'].unique()]
        r = df.set_index('id')['Recipe']
        # because of "manual save", it is necessary to "fill" r df with None values if index doesn't exist for 0-27
        fillv_ = [i for i in range(0, 28) if i not in r.keys()]
        for idx in fillv_:
            r[idx] = None
        for i in range(0, 28):
            pass
        return r_list, \
               r[0], r[1], r[2], r[3], \
               r[4], r[5], r[6], r[7], \
               r[8], r[9], r[10], r[11], \
               r[12], r[13], r[14], r[15], \
               r[16], r[17], r[18], r[19], \
               r[20], r[21], r[22], r[23], \
               r[24], r[25], r[26], r[27]


@app.callback(Output('sat_ll','options'), Output('sat_lb','options'),
              Output('sat_dl','options'), Output('sat_db','options'),
              Output('sun_ll','options'), Output('sun_lb','options'),
              Output('sun_dl','options'), Output('sun_db','options'),
              Output('mon_ll','options'), Output('mon_lb','options'),
              Output('mon_dl','options'), Output('mon_db','options'),
              Output('tue_ll','options'), Output('tue_lb','options'),
              Output('tue_dl','options'), Output('tue_db','options'),
              Output('wed_ll','options'), Output('wed_lb','options'),
              Output('wed_dl','options'), Output('wed_db','options'),
              Output('thu_ll','options'), Output('thu_lb','options'),
              Output('thu_dl','options'), Output('thu_db','options'),
              Output('fri_ll','options'), Output('fri_lb','options'),
              Output('fri_dl','options'), Output('fri_db','options'),
              Output('cook_time_chart_div', 'children'),
              Input('recipe_select', 'value'),
              prevent_initial_call=True)
def update_week_recipe_list(recipes_selected):

    optns_list = [{'label': recipe, 'value': recipe} for recipe in recipes_selected]

    recipes_db_l = recipes_db()
    recipes_selected_ = [r for r in recipes_selected if r not in EXCL_REC]
    recipes_db_l = recipes_db_l.loc[recipes_db_l['Recipe'].isin(recipes_selected_),
                                    ['Recipe', 'PrepTimeMins', 'CookTimeMins']]
    recipes_db_l = recipes_db_l.drop_duplicates()
    recipes_db_l['TotalMins'] = recipes_db_l['PrepTimeMins'] + recipes_db_l['CookTimeMins']
    recipes_db_l.sort_values(by='TotalMins', inplace=True)
    recipes_db_l = recipes_db_l.drop(columns=['TotalMins'])

    try:
        fig = px.bar(recipes_db_l,
                     y='Recipe',
                     x=['PrepTimeMins', 'CookTimeMins'],
                     orientation='h',
                     labels={
                         'value': 'Minutes',
                         'variable': 'Prep/Cook Time'
                     },
                     color_discrete_map={'PrepTimeMins': 'orangered', 'CookTimeMins': 'lightsalmon'}
                     )
        div = dcc.Graph(
            id='cook_time_graph',
            figure=fig
        )
    except:
        div = dbc.Alert("No recipes selected...", color="warning")
    # recipe_options = dd_options('Recipe', recipes_db_l)
    return optns_list, optns_list, optns_list, optns_list, \
           optns_list, optns_list, optns_list, optns_list, \
           optns_list, optns_list, optns_list, optns_list, \
           optns_list, optns_list, optns_list, optns_list, \
           optns_list, optns_list, optns_list, optns_list, \
           optns_list, optns_list, optns_list, optns_list, \
           optns_list, optns_list, optns_list, optns_list, \
           div
           # recipe_options


@app.callback(Output('shopping_list_table', 'data'),
              [Input('sat_ll','value'), Input('sat_lb','value'),
               Input('sat_dl','value'), Input('sat_db','value'),
               Input('sun_ll','value'), Input('sun_lb','value'),
               Input('sun_dl','value'), Input('sun_db','value'),
               Input('mon_ll','value'), Input('mon_lb','value'),
               Input('mon_dl','value'), Input('mon_db','value'),
               Input('tue_ll','value'), Input('tue_lb','value'),
               Input('tue_dl','value'), Input('tue_db','value'),
               Input('wed_ll','value'), Input('wed_lb','value'),
               Input('wed_dl','value'), Input('wed_db','value'),
               Input('thu_ll','value'), Input('thu_lb','value'),
               Input('thu_dl','value'), Input('thu_db','value'),
               Input('fri_ll','value'), Input('fri_lb','value'),
               Input('fri_dl','value'), Input('fri_db','value'),
               Input('manual_save_button', 'n_clicks')],
              State('week_select', 'value')
              )
def shopping_list_update(a1, b1, c1, d1,
                         a2, b2, c2, d2,
                         a3, b3, c3, d3,
                         a4, b4, c4, d4,
                         a5, b5, c5, d5,
                         a6, b6, c6, d6,
                         a7, b7, c7, d7,
                         n, weekdate):
    meal_list = [a1, b1, c1, d1,
                 a2, b2, c2, d2,
                 a3, b3, c3, d3,
                 a4, b4, c4, d4,
                 a5, b5, c5, d5,
                 a6, b6, c6, d6,
                 a7, b7, c7, d7]
    shopping_list_raw = pd.DataFrame(meal_list, columns=['Recipe'])
    shopping_list = shopping_list_raw.dropna().groupby('Recipe').size().reset_index(name='Meals')
    shopping_list = shopping_list.merge(recipes_db(), how='inner', left_on='Recipe', right_on='Recipe')
    shopping_list['Quantity'] = shopping_list['Meals']*shopping_list['Quantity']/shopping_list['Servings']
    shopping_list.sort_values(by=['Location','Ingredient'], ascending=False, inplace=True)
    shopping_list = shopping_list[~shopping_list.Recipe.isin(EXCL_REC)]

    # store data
    shopping_list_raw['Week'] = str(weekdate)
    shopping_list_raw['TS'] = dt.datetime.now().strftime('%Y%m%d%H%M%S')
    sl_store = shopping_list_raw[~shopping_list_raw['Recipe'].isnull()]
    if sl_store.shape[0] >= round((7 * 2 * NO_OF_PERSONS) * REQD_FILL_PCT) or dash_context() == 'manual_save_button':
        # check if there was an update...
        week_meals_new = sl_store.reset_index()[['Recipe']]
        week_meals_old = meal_plan(weekdate).reset_index()[['Recipe']]
        if not(week_meals_new.equals(week_meals_old)):
            print("Save Week")
            print(sl_store.head())
            sl_store.to_csv('data/sl_store.txt', mode='a', header=False)  # dev

    return shopping_list.to_dict('records')


@app.callback(Output('copied_alert', 'is_open'),
              Input('shopping_list_copy_btn', 'n_clicks'),
              [State('shopping_list_table', 'data'),
               State('shopping_list_copy_btn', 'n_clicks')],
              prevent_initial_call=True)
def copy_shopping_list(n, data, is_open):
    sldf_ = pd.DataFrame(data)
    sldf = sldf_[['Ingredient', 'Quantity', 'Units', 'Recipe']]
    sldf['Recipe'] = sldf['Recipe'].apply(lambda i: '('+i+')')
    sldf.to_clipboard(sep='\t', index=False, header=False)
    return True


# ---- RECIPE EDITOR ------!
@app.callback(Output('r_months_select', 'value'), Input('r_seasons_select', 'value'))
def mths_sel(season):
    if season:
        return season_map[season]
    else:
        return []


@app.callback(Output('recipe_ingr_select', 'value'),
              Input("recipe_editor_select", "value"))
def add_recipe(rec_sel):
    if rec_sel:
        rec_info = get_recipe_info(rec_sel)['Data']
        item_values = [i['value'] for i in dd_options('Ingredient', rec_info)]
        return item_values
    return []


@app.callback(Output('recipe_ingr_table', 'data'),
              [Input('recipe_ingr_select', 'value'),
               Input('recipe_ingr_table', 'data_timestamp')],
              [State('recipe_ingr_table', 'data'),
               State('recipe_editor_select', 'value')])
def populate_ingredients_tbl(items, tbl_upd_timestamp, original_data_tbl, rec_sel):
    if not items:
        return phdf_rec_ingr_tbl.to_dict('records')

    # take in what has already been input (as long as it's still in the item list), and don't change the value

    # items already in table
    odf = pd.DataFrame(original_data_tbl)
    odf = odf[odf['Ingredient'].isin(items)]

    # new items (from recipes) U/C\
    r = get_recipe_info(rec_sel)
    print(r)
    sdf = r['Data']
    sdf = sdf[~sdf['Ingredient'].isin(odf['Ingredient'].unique())]  # exclude if already loaded.

    exist_fams = set(odf['Ingredient'].unique())  # .union(set(sdf['Ingredient'].unique()))

    d = [{'Ingredient': item,
          'Quantity': 1,
          'Units': 'medium',
          'Sub Group': 0
          }
         for item in items if item not in exist_fams
         ]
    ndf = pd.DataFrame(d)
    # df = pd.concat([odf, sdf, ndf])
    df = pd.concat([odf, ndf])
    return df.to_dict('records')


@app.callback(Output('rec_saved_alert', 'is_open'),
              Input('save_recipe_btn', 'n_clicks'),
              [State('recipe_ingr_table', 'data'),
               State('r_book_select', 'value'),
               State('r_page_select', 'value'),
               State('r_name_input', 'value'),
               State('r_servings_select', 'value'),
               State('r_preptime_select', 'value'),
               State('r_cooktime_select', 'value'),
               State('r_months_select', 'value'),
               State('r_tag_select', 'value')],
              prevent_initial_call=True)
def save_recipe(n, data, book, page, name, servings, prep_time, cook_time, months, tags):
    global recipes_db
    if valid_rec(book, page, name, servings, prep_time, cook_time):
        # main rec data
        recipes_db_l = recipes_db()
        rec_df = pd.DataFrame(data)
        rec_df['RecipeCode'] = get_rec_id(book, page)
        rec_df['Recipe'] = name
        rec_df['Servings'] = servings
        rec_df['PrepTimeMins'] = prep_time
        rec_df['CookTimeMins'] = cook_time
        rec_df = rec_df.merge(ingredients_db[['Name', 'Location']].rename(columns={'Name': 'Ingredient'}))
        print(recipes_db_l.shape)
        recipes_db_l = pd.concat([recipes_db_l,rec_df])
        print(recipes_db_l.shape)
        recipes_db_l.to_csv('data/recipes.csv', index=False)
        # rec tags data
        if tags:
            tags_old = pd.read_csv('data/recipes_tags.csv')
            tags_new = pd.DataFrame(data={
                'RecipeCode': [get_rec_id(book, page)] * len(tags),
                'Tags': tags
            })
            tags_df = pd.concat([tags_old, tags_new])
            tags_df.to_csv('data/recipes_tags.csv', index=False)
        # rec months data
        if months:
            months_old = pd.read_csv('data/recipes_months.csv')
            months_new = pd.DataFrame(data={
                'RecipeCode': [get_rec_id(book, page)] * len(months),
                'Months': months
            })
            months_df = pd.concat([months_old, months_new])
            months_df.to_csv('data/recipes_months.csv', index=False)
        return True
    return False


if __name__ == '__main__':
    app.run_server(debug=True)