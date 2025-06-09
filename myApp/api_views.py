from rest_framework import viewsets
from rest_framework.response import Response
from .models import Contact, OAuthState, GoogleAuth
from .serializers import ContactSerializer
from .permissions import IsOwner
from rest_framework.decorators import action, api_view
from .views import export_now, import_now, create_google_credentials, get_google_authorization_url, handle_callback_and_googleauth
from django.shortcuts import redirect
from django.urls import reverse



REDIRECT_URI = 'http://localhost:8000/api/oauth2callback/'



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
            return redirect(reverse('api:authorize'))

        contacts = create_google_credentials(google_auth)
        return Response({'contacts': contacts})


@api_view(['GET'])
def authorize(request):
    authorization_url, temp_user_token = get_google_authorization_url(REDIRECT_URI)
    return Response({
        'auth_url': authorization_url,
        'temp_token': temp_user_token
    })


@api_view(['GET'])
def oauth2callback(request):
    state = request.query_params.get('state')
    code = request.query_params.get('code')
    handle_callback_and_googleauth(request, state, code, REDIRECT_URI)
    return Response({'success': 'Google credentials saved. You can now call the API.'})
