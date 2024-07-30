from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg   

class Reading(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    systolic = models.IntegerField()
    diastolic = models.IntegerField()
    pulse = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    country = models.CharField(max_length=100) 
    sex = models.CharField(max_length=10) 
    country_avg_systolic = models.FloatField()
    country_avg_diastolic = models.FloatField()
    
    # Fields for country and global averages
    country_avg_systolic = models.FloatField(default=0)
    country_avg_diastolic = models.FloatField(default=0)
    global_avg_systolic = models.FloatField(default=0)
    global_avg_diastolic = models.FloatField(default=0)
    
    def save(self, *args, **kwargs):
        super().save(*args,**kwargs)
        # Update country and global averages
        self.update_averages()
        
    def update_averages(self):
        """
        Function to update the averages of country and global as new data is entered by users
        """
        #Update country averages
        country_readings = Reading.objects.filter(country=self.country)
        self.country_avg_systolic = country_readings.aggregate(Avg('systolic'))['systolic__avg']
        self.country_avg_diastolic = country_readings.aggregate(Avg('diastolic'))['diastolic__avg']
        
        # Update global averages
        global_readings = Reading.objects.all()
        self.global_avg_systolic = global_readings.aggregate(Avg('systolic'))['systolic__avg']
        self.global_avg_diastolic = global_readings.aggregate(Avg('diastolic'))['diastolic__avg']
        
        super().save(update_fields=['country_avg_systolic', 'country_avg_diastolic', 'global_avg_systolic', 'global_avg_diastolic'])

    def __str__(self):
        return f"{self.user} - {self.timestamp} - {self.systolic}/{self.diastolic}"
    
    