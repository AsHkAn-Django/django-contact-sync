from rest_framework import generics
from .models import Contact
from .serializers import ContactSerializer
from .permissions import IsOwner


class ContactListAPIView(generics.ListCreateAPIView):
    serializer_class = ContactSerializer
    
    def get_queryset(self):
        return Contact.objects.filter(author=self.request.user)    


class ContactDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContactSerializer
    permission_classes = (IsOwner,)
    
    def get_queryset(self):
        return Contact.objects.filter(author=self.request.user)    
