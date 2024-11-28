import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data import recipes_db, recipes_full, open_ai_bootstrap
import dash
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tabulate import tabulate
#import openai
from openai import OpenAI
import pyperclip

from creds import GMAIL_CREDS, MP_KEY

# TODAY = datetime.date
FULL_REC_OVERWRITE_MODE = False
client = OpenAI(
    api_key=MP_KEY
)


def get_startdate(weekoffset=0, fmt_as_code=False):
    day_offset = 5 - datetime.today().weekday()
    day_offset = day_offset + 7*weekoffset
    start_date = datetime.today() + timedelta(days=day_offset)
    if fmt_as_code:
        return start_date.strftime("%Y%m%d")
    return start_date.strftime("%d-%m-%Y")


# filter values in a df field.
def dd_options(field_name, df, date_fmt=False, sort_by_field=None):
    if sort_by_field:
        df_n = df[[field_name, sort_by_field]].groupby(field_name)[sort_by_field].sum().reset_index()\
            .sort_values(by=sort_by_field, ascending=False)
        print(df_n.head())
        return [{'label': optn[0], 'value': optn[0]} for optn in df_n.to_numpy()]

    df_n = df[[field_name]].drop_duplicates()
    if date_fmt:
        list = [{'label': np.datetime_as_string(optn[0], unit='D'), 'value': np.datetime_as_string(optn[0], unit='D')} for optn in df_n.sort_values(by=field_name).to_numpy()]
        return list
    return [{'label': optn[0], 'value': optn[0]} for optn in df_n.to_numpy()]


def dd_range_options(start, end, step=1):
    return [{'label': optn, 'value': optn} for optn in range(start, end+1, step)]


# filter table -- to modify this to remove the error catching. Just let the DF's go to zero.
def dynamic_filter(df, **kwargs):
    fn_df = df.copy()
    for key in kwargs:
        if kwargs[key] is not None and kwargs[key] != []:
            if type(kwargs[key]) is list:
                fn_df = fn_df.loc[fn_df[key].isin(kwargs[key])]
            else:
                fn_df = fn_df.loc[fn_df[key] == kwargs[key]]
    return fn_df


def get_rec_id(bk_cd, pg):
    return bk_cd + str(pg).zfill(3)


def input_rec_status(book, page, name, servings, prep_time, cook_time):
    # 1. test whether all values filled: if not all necessary values are filled, return "no_save mode" i.e. 0
    if book is None or page is None or name is None or servings is None or prep_time is None or cook_time is None:
        print("Missing some necessary fields!")
        return 0
    # 2. test whether code exists already
    #   2a. if recipe exists & name is identical to old name, return "overwrite mode" i.e. 1
    #   2b. if recipe exists & name is not identical to old name, return "no_save mode" i.e. 0
    #   2c. if recipe exists & name is not identical to old name
    #       BUT FULL_REC_OVERWRITE_MODE is active, return "overwrite mode" i.e. 1
    rec_id = get_rec_id(book, page)
    if rec_id in list(recipes_db()['RecipeCode'].unique()):
        df = recipes_db()[['RecipeCode', 'Recipe']]
        cur_rec_name = df.loc[df['RecipeCode'] == rec_id].drop_duplicates(ignore_index=True)['Recipe'][0]
        print("Recipe Code Exists...")
        if name == cur_rec_name or FULL_REC_OVERWRITE_MODE:
            print("-> Allow Overwrite of {} (overwrite mode = {})!".format(cur_rec_name, FULL_REC_OVERWRITE_MODE))
            return 1
        else:
            print("-> Overwrite blocked because of mismatching name!")
            return 0
    print("New (Valid) Recipe Identified!")
    return 2


def dash_context():
    ctx = dash.callback_context
    return ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None


def get_recipe_info(rec_name):
    # see Sandbox for details.
    rs = recipes_full()
    rs = rs[rs['Recipe'] == rec_name]
    rs_v = {
        'Name': rs['Recipe'].values[0],
        'Code': rs['RecipeCode'].values[0],
        'Book': rs['RecipeCode'].values[0][0:2],
        'Page': rs['RecipeCode'].values[0][2:5],
        'Svgs': rs['Servings'].values[0],
        'PpTm': rs['PrepTimeMins'].values[0],
        'CkTm': rs['CookTimeMins'].values[0],
        'Tags': [t for t in rs['Tags'].unique() if t is not np.nan],
        'Mths': [m for m in rs['Months'].unique() if m is not np.nan],
        'Data': rs[['Ingredient', 'Units', 'Quantity', 'Sub Group']].drop_duplicates()  #.to_dict('records')
    }
    return rs_v


def df_remove_id(df, rec_code):
    return df.drop(df[df['RecipeCode'] == rec_code].index)


def generateChatGPT(context, input, few_shots = pd.DataFrame(), debug = False):
    # "role: system" is basically the context, you describe what the model is expected to do
    messages = [
        {
            "role": "system",
            "content": context
        }
    ]
    # "few shots" examples are a good way to control the output on new data
    # generally the more the better but also keep it low enough to not use too many tokens
    for i, x in few_shots.iterrows():
        messages += [
            {
                "role": "user",
                "content": x.input
            },
            {
                "role": "assistant",
                "content": x.output
            }
        ]
    # the actual
    messages += [
        {
            "role": "user",
            "content": str(input)
        }
    ]
    if debug:
        print(messages)
    # refer to the documentation for more parameters to play with
    response = client.chat.completions.create(
        model = "gpt-4o-mini", # model selection, see possible models online
        temperature = .1, # basically the randomness of the response
        messages = messages
    )
    return response.choices[0].message.content.strip()


def shopping_list_gen_ai(data):
    # non-ai version
    if MP_KEY == '' or MP_KEY is None:
        sldf_ = pd.DataFrame(data)
        sldf = sldf_[['Ingredient', 'Quantity', 'Units', 'Recipe']]
        sldf['Recipe'] = sldf['Recipe'].apply(lambda i: '(' + i + ')')
        sldf['Units'] = sldf['Units'].apply(lambda i: i.replace("\r", ""))
        sldf.to_clipboard(excel=True, sep='\t', index=False, header=False)
        return

    # ai version
    msg_to_save = generateChatGPT(
        """You are an assistant that will take a raw data of ingredients, quantities, recipes, and other information, 
        and consolidate it into a shopping list. Only return the shopping list in list form, including the recipe 
        which needs it.
        """,
        data,
        few_shots=open_ai_bootstrap
    )
    pyperclip.copy(msg_to_save)
    print(data)
    print(pyperclip.paste())
    return


def send_df(df, codes, addn_notes, user):
    gmail_user = GMAIL_CREDS['ACCT']
    gmail_password = GMAIL_CREDS['PWD']

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Meal Plan - {}".format(datetime.date(datetime.now()))
    msg['From'] = gmail_user
    msg['To'] = user

    text = "Hi! Meal Plan for the week!"
    html = """
        <html>
        <head>
            <style>
                table, th, td {{
                    border: 2px solid black;
                    border-collapse: collapse;
                    border-color: #140A45;
                    }}
            </style>
        </head>
        <body>
            {}
            <hr>
            {}
            <hr>
            <p>{}<p>
        </body>
        </html>
        """.format(tabulate(df, headers='keys', tablefmt='html', showindex=False),
                   tabulate(codes, headers='keys', tablefmt='html', showindex=False),
                   addn_notes)
    # Record the MIME types of both parts - text/plain and text/html.
    intro_text = MIMEText(text, 'plain')
    table_df = MIMEText(html, 'html')

    msg.attach(intro_text)
    msg.attach(table_df)

    # print(msg.as_string())
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.close()
        print("email sent!")
    except:
        print('Something went wrong...')