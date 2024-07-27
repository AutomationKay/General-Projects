from django.db import models
from django.contrib.auth.models import User

class Reading(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    systolic = models.IntegerField()
    diastolic = models.IntegerField()
    pulse = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    weight = models.FloatField() # in lbs
    height = models.FloatField() # in feet
    age = models.FloatField() # in years

    def __str__(self):
        """
        
        
        """
        return f"{self.user.username} - {self.timestamp}"
    