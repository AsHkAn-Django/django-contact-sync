from rest_framework import viewsets
from rest_framework.response import Response
from .models import Contact
from .serializers import ContactSerializer
from .permissions import IsOwner
from rest_framework.decorators import action
from .views import export_now, import_now
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.shortcuts import redirect



class ContactAPIViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    
    def get_queryset(self):
        return Contact.objects.filter(author=self.request.user)    

    @action(detail=False, methods=['GET'])
    def export_csv(self, request):
        file_path = export_now(request.user)
        return Response(f"Your file has been created at {file_path}")

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        uploaded_file = request.FILES.get('my_file')

        if not uploaded_file or not uploaded_file.name.endswith('.csv'):
            return Response({'error': 'Please upload a valid CSV file.'}, status=400)

        import_now(request.user, uploaded_file.file)        
        return Response({'success': 'Contacts imported successfully!'})

    @action(detail=False, methods=['get'])
    def api_google_contact(self, request):
        if 'credentials' not in request.session:
         return redirect('myApp:authorize')

        creds_data = request.session['credentials']
        creds = Credentials(**creds_data)

        service = build('people', 'v1', credentials=creds)

        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=10,
            personFields='names,emailAddresses,phoneNumbers,addresses'
        ).execute()
        contacts = results.get('connections', [])
        return Response({'contacts': contacts})