import pandas as pd
import sqlalchemy
import pyodbc

recipes_db = pd.read_csv('data/recipes.csv')
ingredients_db = pd.read_csv('data/ingredients.csv')

day_map = {
    'sat': 'Saturday',
    'sun': 'Sunday',
    'mon': 'Monday',
    'tue': 'Tuesday',
    'wed': 'Wednesday',
    'thu': 'Thursday',
    'fri': 'Friday'
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
