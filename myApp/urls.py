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
