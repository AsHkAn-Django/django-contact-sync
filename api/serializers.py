from rest_framework import serializers
from myApp.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Contact
        fields = ('id', 'name', 'phone_number', 'email', 'address', 'author',)