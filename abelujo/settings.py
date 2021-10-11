# -*- coding: utf-8 -*-

# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

import os
import sys
import warnings

import ruamel.yaml

import termcolor

"""
Django settings for abelujo project.

Load custom settings from config.py at the end.

"""

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# see:
# STATIC_ROOT = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static'))

DEBUG = True
if os.path.exists(os.path.join(BASE_DIR, "PROD.txt")):
    DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'db.db',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
# TIME_ZONE = 'America/Chicago'
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'en'

ugettext = lambda s: s
LANGUAGES = (
    ('en', ugettext('English')),
    ('fr', ugettext('Français')),
    ('de', ugettext('German')),
    ('es', ugettext('Castellano')),
    ('ca', ugettext('Catalan')),
)
LOCALE_PATHS = (
    ('locale'),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = 'collectedstatic/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, "static"),  # all that are not related to a certain app
    os.path.join(BASE_DIR, "public"),  # for brunch and vue.
)

STATIC_PDF = STATICFILES_DIRS[1]

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  # looks for "static" in the app folder
    'django.contrib.staticfiles.finders.FileSystemFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(STATIC_ROOT, "images")

# Directory to store generated files (stock export).
EXPORTS_ROOT = os.path.join(STATIC_ROOT, "exports")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '93iyv(*p4t53qb=2#)$1+nnkm*&li%2e@ma6&eu02%&zr27sy('

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        # 'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                "django.core.context_processors.tz",
                "search.context_processors.global_settings",  # give global settings to templates
            ],
            'loaders': [
                ('pyjade.ext.django.Loader', (
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ))
            ],
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    # i18n in url patterns
    # (before CommonMiddleware for i18n urls withouth a trailing slash to redict correcly).
    # see https://stackoverflow.com/questions/8092695/404-on-requests-without-trailing-slash-to-i18n-urls
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # warning: csrf disabled.
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'abelujo.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'abelujo.wsgi.application'

if os.environ.get('MOD_WSGI_DEBUGGER_ENABLED'):
    # Useful to fall on a pdb prompt on an exception, whith debug-mode
    # and enable-debugger options.
    # http://blog.dscpl.com.au/2015/05/using-modwsgi-express-as-development.html
    DEBUG_PROPAGATE_EXCEPTIONS = True

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # for intcomma currency filter only (card show).
    'django_extensions',
    'bootstrap3',
    'bootstrap_admin',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    # Custom:
    'django_q',
    'rest_framework',

    'search',
)

if not DEBUG:
    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)  # sentry

SESSION_ENGINE = 'django.contrib.sessions.backends.file'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
venv = os.environ.get('VIRTUAL_ENV', 'abelujo default tag')
# this venv is used as a token to differentiate client installations in the logs.
if venv:
    venv = os.path.split(venv)[-1]
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s [%(name)s] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logging.log'),
        },
        'sentry': {
            'level': 'WARNING',  # To capture more than ERROR, change to WARNING, INFO, etc.
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'tags': {'custom-tag': venv},
        },

    },
    'loggers': {
        'debug_logger': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'WARNING',
            'propagate': True,
        },

        # catch all:
        '': {
            'handlers': ['mail_admins', 'console', 'file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'sentry_logger': {
            'handlers': ['file', 'sentry'],
            'level': 'WARNING',
            'propagate': True,
        }

    }
}

LOGIN_URL = "/login/"

# BOOTSTRAP_BASE_URL = '/static/'  # 2021-03: still needed after removal of BOOTSTRAP3 ?

# djangoq task queue: use django's ORM as message broker: simple.
Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default'
}

# private token for Sentry. It is sent to the server by a fabric task.
RAVEN_CONFIG = {}
raven_sentry_file = os.path.join(BASE_DIR, "sentry.txt")
if os.path.exists(raven_sentry_file):
    dsn = ""
    with open(raven_sentry_file, "r") as f:
        dsn = f.read()

        RAVEN_CONFIG = {
            'dsn': dsn,
        }

warnings.simplefilter('ignore', ruamel.yaml.error.UnsafeLoaderWarning)

#
# Speed up tests
#
# 19.38s VS 18.48s += 20% :)
if DEBUG:
    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )

    # logging.disable(logging.CRITICAL)

# long migrations to setup tests?
# https://stackoverflow.com/questions/36487961/django-unit-testing-taking-a-very-long-time-to-create-test-database
TESTING = 'test' in sys.argv[1:]
if TESTING:
    # Also: use pytest.
    print('==================================')
    print('In TEST Mode - Migrations disabled')
    print('==================================')

    class DisableMigrations(object):

        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            # With django 2.1 I had to change return "notmigrations" to return None, otherwise it complained that ModuleNotFoundError: No module named 'notmigrations' – frnhr Jun 11 '19 at 17:58

            return "notmigrations"

    MIGRATION_MODULES = DisableMigrations()

###################################################
# Load all available distributors from Dilicom data.
###################################################

# GLN -> name, address
DILICOM_DISTRIBUTORS = {}
csvfile = "documents/annuaire_distributeurs.csv"
if os.path.exists(csvfile):
    lines = []
    with open(csvfile, 'r') as f:
        lines = f.readlines()

    try:
        for line in lines:
            gln, name, postal_code, city, country, nb_titles, via_dilicom = line.split(";")
            DILICOM_DISTRIBUTORS[gln] = {
                'name': name.strip(),
                'postal_code': postal_code.strip(),
                'city': city.strip(),
                'country': country.strip(),
                'nb_titles': nb_titles.strip(),
                'via_dilicom': via_dilicom.strip(),
            }
        print("INFO: loaded {} distributors into settings.DILICOM_DISTRIBUTORS".format(len(lines)))
    except Exception as e:
        print("WARN: could not load this distributor line: {}".format(line))

else:
    print('INFO: did not find the CSV with all distributors. File {} does not exist'.format(csvfile))

###################################################
# Load all available THEMES
###################################################

# code -> name
CLIL_THEMES = {}
CLIL_THEME_HIERARCHIES = {}
csvfile = "documents/theme-names.csv"
csv_theme_hierarchies = "documents/theme-hierarchies.csv"

if os.path.exists(csvfile):
    lines = []
    with open(csvfile, 'r') as f:
        lines = f.readlines()

    try:
        for line in lines:
            # split and assigment fails with accents in code, not in ipdb.
            # shitty Python or shitty me?
            line = line.decode('utf8')
            code, name = line.split(";")
            CLIL_THEMES[code] = name.strip()
        print("INFO: loaded {} themes into settings.CLIL_THEMES".format(len(lines)))
    except Exception as e:
        print("WARN: could not load this theme line: {}".format(line))

    lines = []
    if os.path.exists(csv_theme_hierarchies):
        with open(csv_theme_hierarchies, 'r') as f:
            lines = f.readlines()
    else:
        print('DEBUG: theme file {} does not exist.'.format(csv_theme_hierarchies))

    for line in lines:
        try:
            line = line.decode('utf8')
            # original code, parent codes, until finish by the same code.
            code, c1, c2, c3, c4 = line.split(";")
            CLIL_THEME_HIERARCHIES[code] = [c1, c2, c3, c4]
        except Exception as e:
            print("WARN: loading theme-hierarchies: could not load this line: {}\n{}".format(line, e))

else:
    print('INFO: did not find the CSV with all themes. File {} does not exist'.format(csvfile))

#########################################################
# Load user settings.
#########################################################

## Default settings:
# If True, don't bother user custom shelf names, use Dilicom's CLIL themes.
USE_THEMES_FOR_SHELVES = False

# User locale for CSV exports.
# Change the decimal separator (point to comma).
LOCALE_FOR_EXPORTS = "fr"


#
# Feature flags
#
# Show a reservation button on the card page.
FEATURE_SHOW_RESERVATION_BUTTON = True

#
# Electre API
#
FEATURE_ELECTRE_API = False

def dilicom_enabled():
    return os.getenv('DILICOM_PASSWORD') is not None \
        and os.getenv('DILICOM_USER') is not None

def dilicom_ftp_enabled():
    """
    The username is different than the FEL À LA DEMANDE.
    """
    return os.getenv('DILICOM_FTP_USER') is not None

def electre_enabled():
    return os.getenv('ELECTRE_PASSWORD') is not None \
        and os.getenv('ELECTRE_USER') is not None


if dilicom_enabled():
    print(termcolor.colored("FEATURE: DILICOM ENABLED", "green"))
if dilicom_ftp_enabled():
    print(termcolor.colored("FEATURE: dilicom FTP enabled", "green"))


if os.path.exists(os.path.join(BASE_DIR, "config.py")):
    try:
        import config  # noqa: F401
    except Exception as e:
        print("Could not load user config.py: {}".format(e))

    try:
        if config:
            if hasattr(config, 'FEATURE_SHOW_RESERVATION_BUTTON'):
                FEATURE_SHOW_RESERVATION_BUTTON = config.FEATURE_SHOW_RESERVATION_BUTTON
                print(termcolor.colored("FEATURE: FEATURE_SHOW_RESERVATION_BUTTON", "green"))

            if hasattr(config, 'FEATURE_ELECTRE_API'):
                FEATURE_ELECTRE_API = config.FEATURE_ELECTRE_API
    except Exception:
        pass


if FEATURE_ELECTRE_API:
    if not electre_enabled():
        print(termcolor.colored("WARN: no username/password for Electre API", "red"))
    else:
        print(termcolor.colored("FEATURE ENABLED: FEATURE_ELECTRE_API", "green"))

print "INFO: Abelujo running on {}".format(os.getcwd())

# Exclude cards for the website (catalogue).
FEATURE_EXCLUDE_FOR_WEBSITE = False
if os.path.exists(os.path.join(BASE_DIR, "config.py")):
    try:
        if config:
            if hasattr(config, 'FEATURE_EXCLUDE_FOR_WEBSITE'):
                FEATURE_EXCLUDE_FOR_WEBSITE = config.FEATURE_EXCLUDE_FOR_WEBSITE
                print(termcolor.colored("FEATURE: FEATURE_EXCLUDE_FOR_WEBSITE", "cyan"))
    except Exception:
        pass

# Stripe checkout integration
FEATURE_STRIPE_CHECKOUT = False
STRIPE_SECRET_API_KEY = ""
STRIPE_WEBHOOK_SECRET = ""
if os.path.exists(os.path.join(BASE_DIR, "config.py")):
    try:
        if config:
            if hasattr(config, 'FEATURE_STRIPE_CHECKOUT'):
                FEATURE_STRIPE_CHECKOUT = config.FEATURE_STRIPE_CHECKOUT
                print(termcolor.colored("FEATURE: FEATURE_STRIPE_CHECKOUT", "yellow"))
            if FEATURE_STRIPE_CHECKOUT:
                if hasattr(config, 'STRIPE_SECRET_API_KEY'):
                    STRIPE_SECRET_API_KEY = config.STRIPE_SECRET_API_KEY
                if not STRIPE_SECRET_API_KEY:
                    print(termcolor.colored('No Stripe secret key found', 'red'))
                else:
                    print(termcolor.colored('Stripe secret key: OK', 'green'))
                if hasattr(config, 'STRIPE_WEBHOOK_SECRET'):
                    STRIPE_WEBHOOK_SECRET = config.STRIPE_WEBHOOK_SECRET
                if not STRIPE_WEBHOOK_SECRET:
                    print(termcolor.colored('No Stripe Webhook secret found', 'red'))
                else:
                    print(termcolor.colored('Stripe webhook secret: OK', 'green'))
    except Exception as e:
        print(e)
        pass

def get_from_config(key, verbose=True, msg="{}: {}", color="green", secret=False):
    if os.path.exists(os.path.join(BASE_DIR, "config.py")):
        try:
            if config:
                if hasattr(config, key):
                    print("--- got {}: {}".format(key, getattr(config, key)))
                    val = getattr(config, key)
                    if val is None:
                        print(termcolor.colored("warn: {} is None", "red"))
                    if color is not None:
                        if secret:
                            val = "OK"
                        msg = msg.format(key, val)
                        print(termcolor.colored(msg, color))
                    return val
        except Exception:
            pass


# Email settings.
# The sender must be verified.
FEATURE_MAILER = True
EMAIL_SENDER = 'contact+commandes@abelujo.cc'
EMAIL_BOOKSHOP_RECIPIENT = None
TEST_EMAIL_BOOKSHOP_RECIPIENT = None
BOOKSHOP_OWNER_NAME = None  # for emails
TEST_BOOKSHOP_OWNER_NAME = None  # for emails
SENDGRID_API_KEY = ""  # Secret. Tied to the verified sender.

# It is possible to use custom mail templates,
# especially to send a confirmation to clients that command online.
# The theme project should be cloned in templates/themes/<theme name>.
# The views on mailer.py check if a repository matching this theme name exist.
EMAIL_THEME = None

# val = get_from_config('SENDGRID_API_KEY', secret=True)
# if val:
#    SENDGRID_API_KEY = val

sendgrid_file_path = 'sendgrid.txt'
if FEATURE_MAILER:
    if os.path.exists(sendgrid_file_path):
        key = ""
        with open(sendgrid_file_path, 'r') as f:
            key = f.read()
        if key:
            key = key.strip()

            SENDGRID_API_KEY = key
            print("Sendgrid key from file: OK")
        else:
            print(termcolor.colored("WARN: we want to be able to send emails, but we couldn't find our Sendgrid secret api key.", "red"))
    else:
        print("MAILER feature is DISABLED")

val = get_from_config('EMAIL_BOOKSHOP_RECIPIENT')
if val:
    EMAIL_BOOKSHOP_RECIPIENT = val
val = get_from_config('TEST_EMAIL_BOOKSHOP_RECIPIENT')
if val:
    TEST_EMAIL_BOOKSHOP_RECIPIENT = val

val = get_from_config('BOOKSHOP_OWNER_NAME')
if val:
    BOOKSHOP_OWNER_NAME = val

val = get_from_config('TEST_BOOKSHOP_OWNER_NAME')
if val:
    TEST_BOOKSHOP_OWNER_NAME = val

val = get_from_config('EMAIL_THEME')
if val:
    EMAIL_THEME = val
