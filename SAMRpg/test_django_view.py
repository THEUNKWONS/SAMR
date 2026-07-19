import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'samr_project.settings')
django.setup()

from django.test import Client
from core.models import Usuario

client = Client(SERVER_NAME='127.0.0.1')
# Log in with the doctor or any user
user = Usuario.objects.get(username="doctor@samria.com")
client.force_login(user)

response = client.post(
    '/api/chatbot/',
    data=json.dumps({'message': 'me duele el estomago demasiado'}),
    content_type='application/json'
)

print(response.status_code)
print(response.json())
