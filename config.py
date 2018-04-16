import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'mapsme7.db')
# DATABASE_URI = 'postgresql://localhost/cf_audit'

OVER = False
ADMINS = set([290271])  # Zverik

# Override these (and anything else) in config_local.py
OAUTH_KEY = ''
OAUTH_SECRET = ''
SECRET_KEY = 'sdkjfhsfljhsadf'

try:
    from config_local import *
except ImportError:
    pass
