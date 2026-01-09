from django.db import models

class Label(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#000000')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'labels'
        ordering = ['name']
    
    def __str__(self):
        return self.name
