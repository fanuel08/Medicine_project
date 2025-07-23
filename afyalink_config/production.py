import os
from .settings import * # This imports all settings from your base settings.py file

# --- Production Specific Settings ---

# DEBUG must be False on a live server for security.
DEBUG = False

# This tells Django which website address is allowed to host this app.
ALLOWED_HOSTS = ['jrjunior.pythonanywhere.com']


# --- Whitenoise Static File Configuration ---
# This helps your live server handle static files correctly and efficiently.

# This line adds the Whitenoise functionality into Django's request/response cycle.
# It should be placed right after the SecurityMiddleware.
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# This defines the single folder on the server where Django will collect all static files.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# This sets a more efficient storage engine for static files, which handles compression and caching.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

