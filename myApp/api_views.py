from rest_framework import viewsets
from rest_framework.response import Response
from .models import Contact, OAuthState, GoogleAuth
from .serializers import ContactSerializer
from .permissions import IsOwner
from rest_framework.decorators import action, api_view
from .views import export_now, import_now
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.shortcuts import redirect
import secrets
from django.urls import reverse



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
        try:
            google_auth = GoogleAuth.objects.get(user=request.user)
        except GoogleAuth.DoesNotExist:
            return redirect(reverse('api:authorize_google'))
         
        creds = Credentials(
            token=google_auth.access_token,
            refresh_token=google_auth.refresh_token,
            token_uri=google_auth.token_uri,
            client_id=google_auth.client_id,
            client_secret=google_auth.client_secret,
            scopes=google_auth.scopes.split(','),
        )
        
        service = build('people', 'v1', credentials=creds)

        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=10,
            personFields='names,emailAddresses,phoneNumbers,addresses'
        ).execute()
        contacts = results.get('connections', [])
        return Response({'contacts': contacts})
    
    
@api_view(['GET'])
def authorize(request):
    flow = get_google_flow()
    state = secrets.token_urlsafe(32)
    temp_user_token = secrets.token_urlsafe(16)
    OAuthState.objects.create(state=state, temp_user_token=temp_user_token)
    
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=state
    )
    return Response({
        'auth_url': authorization_url,
        'temp_token': temp_user_token
    })


@api_view(['GET'])
def oauth2callback(request):
    state = request.query_params.get('state')
    code = request.query_params.get('code')
    
    if not state or not code:
        return Response({"error": "Missing state or code."}, status=400)

    try:
        oauth_state = OAuthState.objects.get(state=state)
    except OAuthState.DoesNotExist:
        return Response({'error': 'Invalid stete.'}, status=400) 
    
    flow = get_google_flow()
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    credentials = flow.credentials

    GoogleAuth.objects.update_or_create(
        user=request.user,
        defaults={
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': ",".join(credentials.scopes),
            'expiry': credentials.expiry,
        }
    )
    
    oauth_state.delete()

    return Response({'success': 'Google credentials saved. You can now call the API.'})


import os
from google_auth_oauthlib.flow import Flow

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPES = ['https://www.googleapis.com/auth/contacts']
REDIRECT_URI = 'http://localhost:8000/api/oauth2callback/'

def get_google_flow():
    flow = Flow.from_client_secrets_file(
        os.path.join(BASE_DIR, 'credentials.json'),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow