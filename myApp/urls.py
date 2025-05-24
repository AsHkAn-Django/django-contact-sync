from django.urls import path
from . import views

app_name = 'myApp'
urlpatterns = [
    path('contact_edit/<int:pk>/', views.EditContactView.as_view(), name='edit_contact'),
    path('delete_contact/<int:pk>/', views.ContactDeleteView.as_view(), name='delete_contact'),   
    path('contact_list/',views.ContactListView.as_view(), name='contact_list'),
    path('add_contact/', views.AddContactView.as_view(), name='add_contact'),     
    path('', views.IndexView.as_view(), name='home'),

    
]
