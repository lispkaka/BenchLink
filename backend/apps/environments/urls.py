from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EnvironmentViewSet, GlobalTokenViewSet

router = DefaultRouter()
router.register(r'environments', EnvironmentViewSet, basename='environment')
router.register(r'global-tokens', GlobalTokenViewSet, basename='global-token')

urlpatterns = [
    path('', include(router.urls)),
]



