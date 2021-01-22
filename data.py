import pandas as pd
import math
pd.options.mode.chained_assignment = None  # default='warn'
# import sqlalchemy
# import pyodbc


ingredients_db = pd.read_csv('data/ingredients.csv')  # hard coded (unchanging)

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

BOOK_LIST = {
    'HH': 'HH Art of Eating Well',
    'GS': 'GS Good and Simple',
    'EG': 'EG Eat Green',
    'GG': 'GG Get the Glow',
    'DE': 'DE Deliciously Ella',
    'SC': 'SC Slow Cooker 5 Ingr',
    'SF': 'SF Super Food Magazine',
    'LM': 'LM Custom Recipes',
    'BP': 'BP Custom Recipes'
}

day_map = {
    'sat': 'Saturday',
    'sun': 'Sunday',
    'mon': 'Monday',
    'tue': 'Tuesday',
    'wed': 'Wednesday',
    'thu': 'Thursday',
    'fri': 'Friday'
}

season_map = {
    'Winter': ['Dec', 'Jan', 'Feb'],
    'Spring': ['Mar', 'Apr', 'May'],
    'Summer': ['Jun', 'Jul', 'Aug'],
    'Autumn': ['Sep', 'Oct', 'Nov'],
    'All': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
}

phdf_shopping_list = pd.DataFrame(data={
    'Location': ['a', 'a'],
    'Ingredient': ['ABCD', 'ASDF'],
    'Recipe': ['ABCD', 'QWERW'],
    'Quantity': [1.0, 2.0],
    'Units': ['g', 'g'],
    'Sub Group': [0, 0],
    'Meals': [1, 1]
})

phdf_rec_ingr_tbl = pd.DataFrame(data={
    'Ingredient': ['ABCD'],
    'Quantity': [1.0],
    'Units': ['g'],
    'Sub Group': [0]
})


def meal_plan(week='all'):
    load = pd.read_csv('data/sl_store.txt').drop_duplicates()
    load['key'] = load['id']*0.01 + load['TS']
    filter = load.groupby(['id', 'Week']).max().reset_index()
    data = load[load['key'].isin(filter['key'])]

    data['matrix_row'] = data['id'].apply(lambda i: math.floor(i/4))
    data['matrix_col'] = data['id'] - data['matrix_row']*4
    data = data.drop(columns=['key', 'TS'])
    # print(data)
    if week == 'all':
        return data
    else:
        return data[data['Week'] == int(week)]


# recipes_db = pd.read_csv('data/recipes.csv')  # needs to be dynamic
def recipes_db():
    return pd.read_csv('data/recipes.csv')


def recipes_full():
    df = pd.merge(recipes_db(), pd.read_csv('data/recipes_tags.csv'), how='outer')
    df = pd.merge(df, pd.read_csv('data/recipes_months.csv'), how='outer')
    df = df.dropna(subset=['Recipe'])
    return df
