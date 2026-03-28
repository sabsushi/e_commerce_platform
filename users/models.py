# users/models.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):

    class Role(models.TextChoices):
        BUYER  = 'buyer',  'Buyer'
        SELLER = 'seller', 'Seller'

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BUYER)

    def __str__(self):
        return f'{self.user.id} - {self.user.username} ({self.role})'


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)