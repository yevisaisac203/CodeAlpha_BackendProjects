import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
user = User.objects.get(username='admin')
user.set_password('admin123')
user.save()
print('✓ Password set successfully for admin user')
print('  Username: admin')
print('  Password: admin123')
