import os

from dotenv import load_dotenv

load_dotenv('.env')
DEV = int(os.environ.get('DEV'))
OWNER = int(os.environ.get('OWNER'))
TOKEN = os.environ.get('TOKEN')
