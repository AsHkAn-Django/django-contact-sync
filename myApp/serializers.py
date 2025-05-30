from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from .models import Contact



class ContactSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(
        region='TR',
        help_text="Format: +90XXXXXXXXXX",
        style={'placeholder': '+90XXXXXXXXXX'},
        error_messages={
            'invalid': 'Phone number must be in the format: +90XXXXXXXXXX and a valid turkish number!'
        }
    )

    class Meta:
        model = Contact
        fields = ('id', 'name', 'phone_number', 'email', 'address', 'author')
