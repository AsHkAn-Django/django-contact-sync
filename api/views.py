from rest_framework import generics
from myApp.models import Contact
from .serializers import ContactSerializer


class ContactList(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    
