from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.views import generic
from .models import Contact
from .forms import ContactForm, SearchForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
import csv, os, datetime
from io import TextIOWrapper
from .people import get_google_flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.http import HttpResponse

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'



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


def export_to_csv(request):
    '''
    Export all the user's contacts to a csv file.
    '''
    contacts = Contact.objects.filter(author=request.user)
    file_path = get_export_file_path(request.user)
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
        
    return redirect('myApp:contact_list')



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
        file = TextIOWrapper(request.FILES['my_file'], encoding='utf-8')
        reader = csv.DictReader(file)
        for row in reader:
            name = row['name']
            phone_number = row['phone_number']
            email = row['email']
            address = row['address']
            if Contact.objects.filter(phone_number=phone_number, author=request.user).exists():
                pass
            else:
                Contact.objects.create(name=name, 
                                       phone_number=phone_number, 
                                       email=email, 
                                       address=address,
                                       author=request.user)
                
    return redirect('myApp:contact_list')




def authorize(request):
    flow = get_google_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    request.session['state'] = state  
    return redirect(authorization_url)


def oauth2callback(request):
    state = request.session.get('state')
    if not state:
        return HttpResponse("Missing state in session. Please start the login again.")

    flow = get_google_flow()
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    credentials = flow.credentials

    # Store credentials in session (not safe for production; better use a DB or encrypted store)
    request.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return redirect('myApp:google_contacts')


def contacts(request):
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
    return render(request, 'myApp/google_contacts.html', {'contacts': contacts})
