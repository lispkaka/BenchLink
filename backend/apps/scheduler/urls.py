from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScheduleTaskViewSet

router = DefaultRouter()
router.register(r'schedules', ScheduleTaskViewSet, basename='schedule')

urlpatterns = [
    path('', include(router.urls)),
]



