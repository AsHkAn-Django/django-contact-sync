from django.urls import reverse_lazy
from django.shortcuts import redirect, render, get_object_or_404
from django.views import generic
from .models import Contact, GoogleAuth, OAuthState
from .forms import ContactForm, SearchForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
import csv, os, datetime
from io import TextIOWrapper
from .google import get_google_flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse
import secrets
from django.http import JsonResponse, HttpResponseRedirect





os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
REDIRECT_URI = 'http://localhost:8000/oauth2callback/'



class IndexView(generic.TemplateView):
    template_name = "myApp/index.html"
    

class ContactListView(LoginRequiredMixin, generic.ListView):
    model = Contact
    context_object_name = 'contacts'
    template_name = "myApp/contact_list.html"
    
    def get_queryset(self):
        query_set = Contact.objects.filter(author=self.request.user)
        querry = self.request.GET.get('search_body') 
        if querry:
            query_set = query_set.filter(Q(name__icontains=querry) |
                                         Q(phone_number__icontains=querry) |
                                         Q(email__icontains=querry) |
                                         Q(address__icontains=querry))            
        return query_set
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SearchForm(self.request.GET or None)
        return context
    


class AddContactView(LoginRequiredMixin, generic.CreateView):
    model = Contact
    form_class = ContactForm
    template_name = "myApp/add_contact.html"
    success_url = reverse_lazy('myApp:contact_list')
    
    def form_valid(self, form):        
        form.instance.author = self.request.user       
        return super().form_valid(form)



class EditContactView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = "myApp/edit_contact.html"
    success_url = reverse_lazy('myApp:contact_list')
    
    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


class ContactDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Contact
    template_name = "myApp/delete_contact.html"
    success_url = reverse_lazy('myApp:contact_list')
    
    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


# -----------EXPORT AND IMPORT-------------

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


# -----------GOOGLE CONTACT-------------


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
    
    