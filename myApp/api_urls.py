from django.urls import path
from rest_framework.routers import SimpleRouter
from . import api_views

myapp = 'api'

router = SimpleRouter()
router.register('', api_views.ContactAPIViewSet, basename='contacts')

urlpatterns = router.urls