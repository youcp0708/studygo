"""
studygo/wsgi.py
WSGI config for studygo project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studygo.settings')

application = get_wsgi_application()
