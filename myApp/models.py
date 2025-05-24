from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField

class Contact(models.Model):
  name = models.CharField(max_length=200)
  phone_number = PhoneNumberField(region='TR')
  email = models.EmailField()
  address = models.CharField(max_length=264)
  author = models.ForeignKey(User, on_delete=models.CASCADE)
  
  def __str__(self):
    return self.name