from rest_framework import viewsets
from rest_framework.response import Response
from .models import Contact
from .serializers import ContactSerializer
from .permissions import IsOwner
from rest_framework.decorators import action
from .views import export_now



class ContactAPIViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    
    def get_queryset(self):
        return Contact.objects.filter(author=self.request.user)    

    @action(detail=False, methods=['GET'])
    def export_csv(self, request):
        file_path = export_now(request.user)
        return Response(f"Your file has been created at {file_path}")
