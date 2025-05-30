from django.urls import path
from . import api_views

myapp = 'api'

urlpatterns = [
    path('', api_views.ContactListAPIView.as_view(), name='contact-list-api'),
    path('<int:pk>/', api_views.ContactDetailAPIView.as_view(), name='contact-detail-api')
]