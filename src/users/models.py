from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        indexes = [
                models.Index(fields=['email']),
                models.Index(fields=['username']),
            ]