from django.urls import path
from rest_framework.routers import SimpleRouter
from . import api_views

app_name = 'api'

router = SimpleRouter()
router.register('contacts', api_views.ContactAPIViewSet, basename='contacts')

urlpatterns = router.urls + [
    path('authorize/', api_views.authorize, name='authorize'),
    path('oauth2callback/', api_views.oauth2callback, name='oauth2callback'),
]