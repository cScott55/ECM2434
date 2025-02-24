from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.conf import settings

class User(AbstractUser):
    USER_TYPES = (
        ('player', 'Player'),
        ('game_keeper', 'Game Keeper'),
        ('developer', 'Developer'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='player')

    score = models.IntegerField(default=0)

# Code for user Profiles:
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# Code for missions:
class Mission(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    points = models.IntegerField(default=10)

    def __str__(self):
        return self.name

class UserMission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    date_completed = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.mission.name}"
        