from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestCaseViewSet, PerformanceTestViewSet

router = DefaultRouter()
router.register(r'testcases', TestCaseViewSet, basename='testcase')
router.register(r'performance-tests', PerformanceTestViewSet, basename='performance-test')

urlpatterns = [
    path('', include(router.urls)),
]



