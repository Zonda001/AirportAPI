from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CrewViewSet, AirportViewSet, RouteViewSet,
    AirplaneTypeViewSet, AirplaneViewSet, FlightViewSet,
    OrderViewSet
)

router = DefaultRouter()
router.register(r'crews', CrewViewSet)
router.register(r'airports', AirportViewSet)
router.register(r'routes', RouteViewSet)
router.register(r'airplane-types', AirplaneTypeViewSet)
router.register(r'airplanes', AirplaneViewSet)
router.register(r'flights', FlightViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
