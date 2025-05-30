from django.urls import path
from . import api_views

myapp = 'api'

urlpatterns = [
    path('', api_views.ContactList.as_view(), name='contact-list')
]