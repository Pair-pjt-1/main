from django.db import models

# Create your models here.
class Crawlings(models.Model):
    title = models.CharField(max_length=20)
    code = models.CharField(max_length=7)
    comment = models.TextField()
    updated_at = models.DateField(auto_now_add=True)