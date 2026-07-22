import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'samr_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
users = []
for u in User.objects.all():
    users.append({
        'username': u.username,
        'password': u.password,
        'tipoUsuario': getattr(u, 'tipoUsuario', 'PACIENTE'),
        'first_name': u.first_name,
        'last_name': u.last_name,
        'email': u.email,
        'is_superuser': u.is_superuser
    })
with open('users_backup.json', 'w') as f:
    json.dump(users, f)
print(f"Dumped {len(users)} users.")
