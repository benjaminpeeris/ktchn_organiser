import pandas as pd
import math
pd.options.mode.chained_assignment = None  # default='warn'
import sqlalchemy
import pyodbc
import urllib
import pymysql

from sql_db_params import user_id, pwd, server_name, db_name

MYSQLengine = sqlalchemy.create_engine('mysql+pymysql://{}:{}@{}/{}'.format(user_id, pwd, server_name, db_name)
                                       , pool_recycle=3600)

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

phdf_meal_summary = pd.DataFrame(data={
    'Recipe': ['Dummy1', 'Dummy2'],
    'Planned Meals': [1, 1],
    'Supplementary Meals': [0, 0]
})

phdf_rec_ingr_tbl = pd.DataFrame(data={
    'Ingredient': ['ABCD'],
    'Quantity': [1.0],
    'Units': ['g'],
    'Sub Group': [0]
})

open_ai_bootstrap = pd.DataFrame([
    ["[{'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Sweet Potatoes', 'Location': 'Market', 'Units': 'large', 'Quantity': 4, 'Sub Group': 0}, {'Recipe': 'Tortilla', 'Meals': 4, 'RecipeCode': 'BP025', 'Servings': 4, 'PrepTimeMins': 5, 'CookTimeMins': 10, 'Ingredient': 'Salad Leaves', 'Location': 'Market', 'Units': 'medium', 'Quantity': 1, 'Sub Group': 0}, {'Recipe': 'Smoky Black Bean Stew', 'Meals': 4, 'RecipeCode': 'DE004', 'Servings': 4, 'PrepTimeMins': 10, 'CookTimeMins': 20, 'Ingredient': 'Onion (Red)', 'Location': 'Market', 'Units': 'medium', 'Quantity': 1, 'Sub Group': 0}, {'Recipe': 'Tortilla', 'Meals': 4, 'RecipeCode': 'BP025', 'Servings': 4, 'PrepTimeMins': 5, 'CookTimeMins': 10, 'Ingredient': 'Onion (Red)', 'Location': 'Market', 'Units': 'medium', 'Quantity': 1, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Lime', 'Location': 'Market', 'Units': 'medium', 'Quantity': 0.5, 'Sub Group': 0}, {'Recipe': 'Smoky Black Bean Stew', 'Meals': 4, 'RecipeCode': 'DE004', 'Servings': 4, 'PrepTimeMins': 10, 'CookTimeMins': 20, 'Ingredient': 'Lime', 'Location': 'Market', 'Units': 'medium', 'Quantity': 1, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Lemon', 'Location': 'Market', 'Units': 'medium', 'Quantity': 0.5, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Garlic', 'Location': 'Market', 'Units': 'medium', 'Quantity': 4, 'Sub Group': 0}, {'Recipe': 'Mac & Cheese', 'Meals': 6, 'RecipeCode': 'BP010', 'Servings': 6, 'PrepTimeMins': 30, 'CookTimeMins': 45, 'Ingredient': 'Garlic', 'Location': 'Market', 'Units': 'medium', 'Quantity': 1, 'Sub Group': 0}, {'Recipe': 'Smoky Black Bean Stew', 'Meals': 4, 'RecipeCode': 'DE004', 'Servings': 4, 'PrepTimeMins': 10, 'CookTimeMins': 20, 'Ingredient': 'Garlic', 'Location': 'Market', 'Units': 'medium', 'Quantity': 2, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Coriander', 'Location': 'Market', 'Units': 'medium', 'Quantity': 1, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Cherry Tomatoes', 'Location': 'Market', 'Units': 'medium', 'Quantity': 24, 'Sub Group': 0}, {'Recipe': 'Tortilla', 'Meals': 4, 'RecipeCode': 'BP025', 'Servings': 4, 'PrepTimeMins': 5, 'CookTimeMins': 10, 'Ingredient': 'Capsicum (Red)', 'Location': 'Market', 'Units': 'medium', 'Quantity': 2, 'Sub Group': 0}, {'Recipe': 'Mac & Cheese', 'Meals': 6, 'RecipeCode': 'BP010', 'Servings': 6, 'PrepTimeMins': 30, 'CookTimeMins': 45, 'Ingredient': 'Beef (Minced)', 'Location': 'Market', 'Units': 'g', 'Quantity': 500, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Avocados', 'Location': 'Market', 'Units': 'medium', 'Quantity': 2, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Yogurt', 'Location': 'Carrefour', 'Units': 'g', 'Quantity': 200, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Vinegar (Apple Cider)', 'Location': 'Carrefour', 'Units': 'tbsp', 'Quantity': 2, 'Sub Group': 0}, {'Recipe': 'Tortilla', 'Meals': 4, 'RecipeCode': 'BP025', 'Servings': 4, 'PrepTimeMins': 5, 'CookTimeMins': 10, 'Ingredient': 'Tortilla Pack', 'Location': 'Carrefour', 'Units': 'medium', 'Quantity': 1, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Tomatoes (Sun Dried)', 'Location': 'Carrefour', 'Units': 'g', 'Quantity': 50, 'Sub Group': 0}, {'Recipe': 'Mac & Cheese', 'Meals': 6, 'RecipeCode': 'BP010', 'Servings': 6, 'PrepTimeMins': 30, 'CookTimeMins': 45, 'Ingredient': 'Tomato Sauce', 'Location': 'Carrefour', 'Units': 'ml', 'Quantity': 400, 'Sub Group': 0}, {'Recipe': 'Smoky Black Bean Stew', 'Meals': 4, 'RecipeCode': 'DE004', 'Servings': 4, 'PrepTimeMins': 10, 'CookTimeMins': 20, 'Ingredient': 'Tomato Puree', 'Location': 'Carrefour', 'Units': 'tbsp', 'Quantity': 1, 'Sub Group': 0}, {'Recipe': 'Smoky Black Bean Stew', 'Meals': 4, 'RecipeCode': 'DE004', 'Servings': 4, 'PrepTimeMins': 10, 'CookTimeMins': 20, 'Ingredient': 'Tomato (Diced, Tin)', 'Location': 'Carrefour', 'Units': 'g', 'Quantity': 400, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Tahini', 'Location': 'Carrefour', 'Units': 'tbsp', 'Quantity': 1, 'Sub Group': 0}, {'Recipe': 'Mac & Cheese', 'Meals': 6, 'RecipeCode': 'BP010', 'Servings': 6, 'PrepTimeMins': 30, 'CookTimeMins': 45, 'Ingredient': 'Macaroni', 'Location': 'Carrefour', 'Units': 'g', 'Quantity': 250, 'Sub Group': 0}, {'Recipe': 'Tortilla', 'Meals': 4, 'RecipeCode': 'BP025', 'Servings': 4, 'PrepTimeMins': 5, 'CookTimeMins': 10, 'Ingredient': 'Chicken (Fillet)', 'Location': 'Carrefour', 'Units': 'g', 'Quantity': 500, 'Sub Group': 0}, {'Recipe': 'Mac & Cheese', 'Meals': 6, 'RecipeCode': 'BP010', 'Servings': 6, 'PrepTimeMins': 30, 'CookTimeMins': 45, 'Ingredient': 'Cheese (Cheddar)', 'Location': 'Carrefour', 'Units': 'g', 'Quantity': 150, 'Sub Group': 0}, {'Recipe': 'Loaded Sweet Potato Skins', 'Meals': 4, 'RecipeCode': 'DE008', 'Servings': 4, 'PrepTimeMins': 25, 'CookTimeMins': 60, 'Ingredient': 'Black Beans', 'Location': 'Carrefour', 'Units': 'g', 'Quantity': 800, 'Sub Group': 0}, {'Recipe': 'Smoky Black Bean Stew', 'Meals': 4, 'RecipeCode': 'DE004', 'Servings': 4, 'PrepTimeMins': 10, 'CookTimeMins': 20, 'Ingredient': 'Black Beans', 'Location': 'Carrefour', 'Units': 'g\r', 'Quantity': 800, 'Sub Group': 0}, {'Recipe': 'Smoky Black Bean Stew', 'Meals': 4, 'RecipeCode': 'DE004', 'Servings': 4, 'PrepTimeMins': 10, 'CookTimeMins': 20, 'Ingredient': 'Almond Butter', 'Location': 'Carrefour', 'Units': 'tbsp', 'Quantity': 1, 'Sub Group': 0}]",
     """Sweet Potatoes 4 large (Loaded Sweet Potato Skins)
Salad Leaves 1 medium (Tortilla)
Onion (Red)	2 medium (Smoky Black Bean Stew / Tortilla)
Lime 1.5 medium (Loaded Sweet Potato Skins / Smoky Black Bean Stew)
Lemon 0.5 medium (Loaded Sweet Potato Skins)
Garlic 7 medium (Loaded Sweet Potato Skins / Mac & Cheese / Smoky Black Bean Stew)
Coriander 1 medium (Loaded Sweet Potato Skins)
Cherry Tomatoes	24 medium (Loaded Sweet Potato Skins)
Capsicum (Red) 2 medium (Tortilla)
Beef (Minced) 500	g (Mac & Cheese)
Avocados 2 medium (Loaded Sweet Potato Skins)
Yogurt	200 g (Loaded Sweet Potato Skins)
Vinegar (Apple Cider) 2 tbsp (Loaded Sweet Potato Skins)
Tortilla Pack 1 medium (Tortilla)
Tomatoes (Sun Dried) 50 g (Loaded Sweet Potato Skins)
Tomato Sauce 400 ml	(Mac & Cheese)
Tomato Puree 1 tbsp	(Smoky Black Bean Stew)
Tomato (Diced, Tin)	400 g (Smoky Black Bean Stew)
Tahini 1 tbsp (Loaded Sweet Potato Skins)
Macaroni 250 g (Mac & Cheese)
Chicken (Fillet) 500 g (Tortilla)
Cheese (Cheddar) 150 g (Mac & Cheese)
Black Beans	800 g (Loaded Sweet Potato Skins)
Black Beans	800.0 g (Smoky Black Bean Stew)
Almond Butter 1 tbsp (Smoky Black Bean Stew)
     """]
], columns=['input', 'output'])


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


