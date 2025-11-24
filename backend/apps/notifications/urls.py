from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationChannelViewSet

router = DefaultRouter()
router.register(r'channels', NotificationChannelViewSet, basename='notification-channel')

urlpatterns = [
    path('', include(router.urls)),
]




