from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    password_verification = models.CharField(max_length=64, null=True)
    reputation = models.IntegerField(default=0)
    
    class Meta:
        db_table = "Form"

class Tip(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    contenu = models.TextField(max_length=64)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    upvote = models.ManyToManyField(User, related_name='upvote')
    downvote = models.ManyToManyField(User, related_name='downvote')
    class Meta:
        db_table = "Tip"
        permissions = [
        ('can_downvote_tip pour correction', 'Can downvote tip pour correction'),
]