from django.urls import path
from . import views

myapp = 'api'

urlpatterns = [
    path('', views.ContactList.as_view(), name='contact-list')
]