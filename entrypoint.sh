#!/bin/sh

# Run migrations
echo "Running migrations..."
uv run python manage.py migrate --noinput

# Seed admin user (only in development)
if [ "$DEBUG" = "True" ]; then
    echo "Seeding admin user..."
    uv run python manage.py shell << 'END'
from django.contrib.auth import get_user_model

User = get_user_model()

# Create admin if doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print('Admin user created: admin/admin123')
else:
    print('Admin user already exists')

# Create test users (optional - for testing API)
test_users = [
    {'username': 'john', 'email': 'john@example.com', 'password': 'test123'},
    {'username': 'jane', 'email': 'jane@example.com', 'password': 'test123'},
]

for user_data in test_users:
    if not User.objects.filter(username=user_data['username']).exists():
        User.objects.create_user(**user_data)
        print(f"✅ Test user created: {user_data['username']}/test123")
END
fi

echo "Starting server..."
uv run python manage.py runserver 0.0.0.0:8000
