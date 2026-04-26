from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    USER_CHOICES = [
            ('SECURITY', 'Security Guard'),('CLEANER', 'Cleaner'),
            ('FRONTEND_DEV', 'Frontend Developer'),('BACKEND_DEV', 'Backend Developer'),
            ('AI_DEV', 'AI Developer'),('FULLSTACK_DEV', 'FullStack Developer'),('DATA_ENTRY' , 'Data Entry')

    ]   
    LEVEL_CHOICES = [
        ('JUNIOR', 'Junior'),
        ('MID', 'Mid-Level'),
        ('SENIOR', 'Senior')
    ]

    image = models.ImageField(upload_to='profile_pics' ,null = True , blank= True)
    phone_number = PhoneNumberField(blank=True, null=True, region="DE", verbose_name="Phone Number")
    street = models.CharField(max_length=255 , null=False , blank=False , verbose_name='Street Name')
    post_number = models.CharField(max_length=10 ,blank=False , null=False , verbose_name='Postal CodeS')
    house_number = models.CharField(max_length=5 ,null=False ,blank=False ,verbose_name='House Number')
    details = models.TextField(null=True )
    user_type = models.CharField(max_length=55 , choices=USER_CHOICES ,default='SECURITY' ,null=False)
    level = models.CharField(max_length=50 ,  choices=LEVEL_CHOICES , default='MID' ,null=False)

    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"
    