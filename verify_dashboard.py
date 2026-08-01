import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sundowns_app.settings.test')
import django
django.setup()
from django.test import Client
from users.models import User

u = User.objects.create_user(username='dbg7', email='dbg7@example.com', password='Xy123456!', role='member')
u.first_name = 'William'
u.save()

c = Client()
c.force_login(u)
resp = c.get('/dashboard/')
print(resp.status_code)
print('Welcome, William!' in resp.content.decode('utf-8'))
