from django.urls import path
from . import views

app_name = 'user_registration'
urlpatterns = [
  path('signup/', views.SignUpView.as_view(), name='signup'),
]
