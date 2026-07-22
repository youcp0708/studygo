import os
import django
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studygo.settings")
django.setup()

from users.models import User, StudentProfile

user = User.objects.first()
if user:
    client = Client()
    client.force_login(user)
    
    # Hit the API with 'vi' language
    response = client.get('/api/flows/my-tasks/', HTTP_ACCEPT_LANGUAGE='vi')
    print("Status Code:", response.status_code)
    try:
        print(response.json())
    except Exception as e:
        print("Response is not JSON:", response.content.decode('utf-8')[:500])
else:
    print("No user found")
