from django.urls import reverse_lazy
from django.views import generic
from .models import Contact
from .forms import ContactForm, SearchForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q

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
