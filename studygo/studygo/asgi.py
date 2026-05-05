"""
studygo/asgi.py
ASGI config for studygo project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studygo.settings')

application = get_asgi_application()
