from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestSuiteViewSet

router = DefaultRouter()
router.register(r'testsuites', TestSuiteViewSet, basename='testsuite')

urlpatterns = [
    path('', include(router.urls)),
]



