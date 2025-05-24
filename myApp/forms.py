from django import forms
from .models import Contact


class ContactForm(forms.ModelForm):
  class Meta:
    model = Contact
    fields = ['name', 'phone_number', 'email', 'address']


class SearchForm(forms.Form):
  search_body = forms.CharField(max_length=264, label='Search')
  
  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.fields['search_body'].widget.attrs['placeholder'] = 'Name, number, address, ...'
  
  
  