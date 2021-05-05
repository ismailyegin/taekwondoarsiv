from oxiterp.settings.base import *

# Override base.py settings here


DEBUG = True
ALLOWED_HOSTS = ['*']

# DATABASES = {
#   'default': {
#      'ENGINE': 'django.db.backends.postgresql',
#     'NAME': 'oxiterp',
#    'USER': 'oxitowner',
#   'PASSWORD': 'oxit2016',
#  'HOST': 'localhost',
# 'PORT': '5432',
# }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tekvandoarsiv2',
        'HOST': 'localhost',
        'PORT': '3306',
        'USER': 'root',
        'PASSWORD': 'kobil2013'
    }
}


STATIC_ROOT = "C:/Users/User/Bitnami Django Stack projects/TaekwondoArsiv/static"

STAICFILES_DIR = [

    "C:/Users/User/Bitnami Django Stack projects/TaekwondoArsiv/static"

]

try:
    from oxiterp.settings.local import *
except:
    pass