# -*- coding: utf-8 -*-

# Copyright 2014 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.
import os

# Django settings for abelujo project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# see:
# STATIC_ROOT = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static'))

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
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
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'en'

ugettext = lambda s:s
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

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = 'static/collected/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, "static"), # all that are not related to a certain app
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder', # looks for "static" in the app folder
    'django.contrib.staticfiles.finders.FileSystemFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '93iyv(*p4t53qb=2#)$1+nnkm*&li%2e@ma6&eu02%&zr27sy('

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('pyjade.ext.django.Loader',(
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
    )),
)

# TEMPLATE_LOADERS = (
#     ('django.template.loaders.filesystem.Loader',
#     'django.template.loaders.app_directories.Loader',
# #     'django.template.loaders.eggs.Loader',
#     ),
# )

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages"
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # warning: csrf disabled.
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # i18n in url patterns:
    'django.middleware.locale.LocaleMiddleware',
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

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, "templates"),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'bootstrap3',
    'bootstrap_admin',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    # Custom:
    'djangular',
    'mod_wsgi.server',
    'search',
)


SESSION_ENGINE = 'django.contrib.sessions.backends.file'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
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
        }

    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', ],
            'level': 'ERROR',
            'propagate': True,
        },

        # catch all:
        '': {
            'handlers': ['mail_admins', 'console'],
            'level': 'WARNING',
            'propagate': True,
        }
    }
}
