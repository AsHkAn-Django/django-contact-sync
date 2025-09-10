# Django Contact Sync

A Django app to manage a contact list with CSV import/export functionality and cloud synchronization (e.g., Google Contacts).

## Features
- Add, edit, and delete contacts
- Import and export contacts as CSV
- Sync contacts with cloud services
- Detect duplicates and validate data


## About Me

Hi, I'm Ashkan — a junior Django developer who recently transitioned from teaching English as a second language to learning backend development.
I’m currently focused on improving my skills, building projects, and looking for opportunities to work as a backend developer.
You can find more of my work here: [My GitHub](https://github.com/AsHkAn-Django)
[Linkdin](in/ashkan-ahrari-146080150)


## How to Use
1. Clone the repository
   `git clone https://github.com/AsHkAn-Django/django-contact-sync.git`
2. Navigate into the folder
   `cd django-contact-sync`
3. Create a virtual environment and activate it
4. Install the dependencies
   `pip install -r requirements.txt`
5. Run the server
   `python manage.py runserver`


## Tutorial

search method
```python
def get_queryset(self):
   query_set = Contact.objects.filter(author=self.request.user)
   querry = self.request.GET.get('search_body')
   if querry:
      query_set = query_set.filter(Q(name__icontains=querry) |
                                    Q(phone_number__icontains=querry) |
                                    Q(email__icontains=querry) |
                                    Q(address__icontains=querry))
```


1. Activating api and Download credentials.json from google contacts api

2. create googel.py
```python
import os
from google_auth_oauthlib.flow import Flow

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPES = ['https://www.googleapis.com/auth/contacts']


def get_google_flow(REDIRECT_URI):
    flow = Flow.from_client_secrets_file(
        os.path.join(BASE_DIR, 'credentials.json'),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow
```

3. creating models to save google creds and states
```python
class GoogleAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_uri = models.TextField()
    client_id = models.TextField()
    client_secret = models.TextField()
    scopes = models.TextField()
    expiry = models.DateTimeField()


class OAuthState(models.Model):
    state = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    temp_user_token = models.CharField(max_length=255, blank=True, null=True)
```

4. I tried to refactor the functions so can be used in both web and api
for web we have:
```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import secrets
from django.http import JsonResponse, HttpResponseRedirect
from .google import get_google_flow

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
REDIRECT_URI = 'http://localhost:8000/oauth2callback/'

def authorize(request):
    authorization_url, _ = get_google_authorization_url(REDIRECT_URI)
    return redirect(authorization_url)

def oauth2callback(request):
    state = request.GET.get('state')
    code = request.GET.get('code')
    handle_callback_and_googleauth(request, state, code, REDIRECT_URI)
    return redirect('myApp:google_contacts')

def get_google_contacts(request):
    google_auth = get_googleauth_or_authorize(request)
    if isinstance(google_auth, HttpResponseRedirect):
        return google_auth
    contacts = create_google_credentials(google_auth)
    return render(request, 'myApp/google_contacts.html', {'contacts': contacts})

def add_contact_from_google(request, pk):
    google_auth = get_googleauth_or_authorize(request)
    if isinstance(google_auth, HttpResponseRedirect):
        return google_auth

    pk = f'people/{pk}'

    creds = Credentials(
        token=google_auth.access_token,
        refresh_token=google_auth.refresh_token,
        token_uri=google_auth.token_uri,
        client_id=google_auth.client_id,
        client_secret=google_auth.client_secret,
        scopes=google_auth.scopes.split(','),
    )

    service = build('people', 'v1', credentials=creds)

    # Fetch a single contact by resourceName (e.g., 'people/c123456')
    contact = service.people().get(
        resourceName=pk,
        personFields='names,emailAddresses,phoneNumbers,addresses'
    ).execute()

    name = contact['names'][0]['displayName'] if 'names' in contact else ''
    phone_number = contact['phoneNumbers'][0]['value'] if 'phoneNumbers' in contact else ''
    email = contact['emailAddresses'][0]['value'] if 'emailAddresses' in contact else ''
    address = contact['addresses'][0]['formattedValue'] if 'addresses' in contact else ''

    if phone_number and not Contact.objects.filter(phone_number=phone_number, author=request.user).exists():
        Contact.objects.create(
            name=name,
            phone_number=phone_number,
            email=email,
            address=address,
            author=request.user
        )
    return redirect('myApp:contact_list')

def add_contact_in_google(request, pk):
    contact = get_object_or_404(Contact, pk=pk)

    google_auth = get_googleauth_or_authorize(request)
    if isinstance(google_auth, HttpResponseRedirect):
        return google_auth
    creds = Credentials(
        token=google_auth.access_token,
        refresh_token=google_auth.refresh_token,
        token_uri=google_auth.token_uri,
        client_id=google_auth.client_id,
        client_secret=google_auth.client_secret,
        scopes=google_auth.scopes.split(','),
    )
    service = build('people', 'v1', credentials=creds)

    contact_body = {}
    if contact.name:
        contact_body['names'] = [{'givenName': contact.name}]
    if contact.phone_number:
        contact_body['phoneNumbers'] = [{'value': str(contact.phone_number)}]
    if contact.address:
        contact_body['addresses'] = [{'formattedValue': contact.address}]
    if contact.email:
        contact_body['emailAddresses'] = [{'value': contact.email}]

    try:
        service.people().createContact(body=contact_body).execute()
    except Exception as e:
        return HttpResponse(f'Google API error: {e}', status=500)
    return redirect('myApp:google_contacts')

def create_google_credentials(google_auth):
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
    return contacts

def get_google_authorization_url(REDIRECT_URI):
    flow = get_google_flow(REDIRECT_URI)
    state = secrets.token_urlsafe(32)
    temp_user_token = secrets.token_urlsafe(16)
    OAuthState.objects.create(state=state, temp_user_token=temp_user_token)

    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=state
    )
    return authorization_url, temp_user_token

def handle_callback_and_googleauth(request, state, code, REDIRECT_URI):
    if not state or not code:
        return JsonResponse({"error": "Missing state or code."}, status=400)

    try:
        oauth_state = OAuthState.objects.get(state=state)
    except OAuthState.DoesNotExist:
        return JsonResponse({'error': 'Invalid stete.'}, status=400)

    flow = get_google_flow(REDIRECT_URI)
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
    return None

def get_googleauth_or_authorize(request):
    try:
        google_auth = GoogleAuth.objects.get(user=request.user)
    except GoogleAuth.DoesNotExist:
        return redirect(reverse('myApp:authorize'))
    return google_auth
```
---
and the urls.py
```python
from django.urls import path
from . import views

app_name = 'myApp'

urlpatterns = [
    path('contact_edit/<int:pk>/', views.EditContactView.as_view(), name='edit_contact'),
    path('delete_contact/<int:pk>/', views.ContactDeleteView.as_view(), name='delete_contact'),
    path('contact_list/export',views.export_to_csv, name='export_contacts'),
    path('contact_list/import',views.import_from_csv, name='import_contacts'),
    path('contact_list/',views.ContactListView.as_view(), name='contact_list'),
    path('add_contact/', views.AddContactView.as_view(), name='add_contact'),
    path('', views.IndexView.as_view(), name='home'),
    path('authorize/', views.authorize, name='authorize'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('google_contacts/', views.get_google_contacts, name='google_contacts'),
    path('google_contacts/add_from_google/<str:pk>/', views.add_contact_from_google, name='add_from_google'),
    path('contact_list/add_contact_in_google/<int:pk>/', views.add_contact_in_google, name='add_contact_in_google'),
]
```

5. for api_views.py we have:
```python
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
```

✅ What is @action?
- The @action decorator creates a custom route for a method inside a ViewSet.

- It's defined inside a ViewSet (like ModelViewSet, ReadOnlyModelViewSet, etc.)

- You specify whether it's for a single object (detail=True) or not (detail=False).

- It allows you to define extra functionality for your resource beyond the typical REST actions.


### for import and export
```python
def export_to_csv(request):
    '''Export all the user's contacts to a csv file.'''
    export_now(request.user)
    return redirect('myApp:contact_list')


def export_now(user):
    contacts = Contact.objects.filter(author=user)
    file_path = get_export_file_path(user)
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['name', 'phone_number', 'email', 'address'])
            writer.writeheader()
            for contact in contacts:
                contacts_dic = {
                    'name':contact.name,
                    'phone_number': contact.phone_number,
                    'email': contact.email,
                    'address': contact.address,
                }
                writer.writerow(contacts_dic)
    except Exception as e:
        print(f"CSV export failed: {e}")
    return file_path


def get_export_file_path(user):
    '''
    Create a folder path and file name base on user's name and date.
    '''
    folder = os.path.join('contact_exports', user.username)
    os.makedirs(folder, exist_ok=True)
    filename = f"contacts_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    return os.path.join(folder, filename)


def import_from_csv(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get('my_file')
        if not uploaded_file or not uploaded_file.name.endswith('.csv'):
            messages.warning(request, 'Please upload a valid CSV file.')
            return redirect('myApp:contact_list')
        import_now(request.user, uploaded_file)
        messages.success(request, 'Contacts were successfully added.')
    return redirect('myApp:contact_list')


def import_now(user, uploaded_file):
    encoded_file = TextIOWrapper(uploaded_file, encoding='utf-8')
    reader = csv.DictReader(encoded_file)
    for row in reader:
        name = row['name']
        phone_number = row['phone_number']
        email = row['email']
        address = row['address']
        if not Contact.objects.filter(phone_number=phone_number, author=user).exists():
            Contact.objects.create(name=name,
                                    phone_number=phone_number,
                                    email=email,
                                    address=address,
                                    author=user)
```
>>>>>>> d47fa3747513d7b803f57002c3a8ce5cbfa59666
