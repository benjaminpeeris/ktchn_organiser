GMAIL_CREDS = {
    'ACCT': 'email_send_from@gmail.com',
    'PWD': 'password'
}

MP_KEY = 'YOUR_OPEN_AI_KEY' # leave as '' to access the non AI version

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

SQL_CREDS = Struct(**{
    "host": "",
    "port": "",
    "login": "",
    "password": "" 
})