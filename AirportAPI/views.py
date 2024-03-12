from datetime import datetime

from django.db.models import Value, Count, F
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Crew, Airport, Route, AirplaneType, Airplane, Flight, Order,
)
from .serializers import (
    CrewSerializer, AirportSerializer, RouteListSerializer, RouteCreateSerializer,
    RouteDetailSerializer, AirplaneTypeSerializer, AirplaneListSerializer,
    AirplaneCreateSerializer, AirplaneDetailSerializer, FlightListSerializer,
    FlightCreateSerializer, FlightDetailSerializer, OrderCreateSerializer,
    OrderListSerializer, OrderDetailSerializer,
)


class ResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 1000


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        full_name = self.request.query_params.get("full_name")
        if full_name:
            queryset = queryset.annotate(
                full_name=Concat("first_name", Value(" "), "last_name")
            ).filter(full_name__icontains=full_name)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "full_name",
                type=str,
                description="Filtering by full_name (ex. ?full_name=Vika Bevz)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=str,
                description="Filtering by name (ex. ?name=Kansas)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source", "destination")
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        source_name = self.request.query_params.get("from")
        destination_name = self.request.query_params.get("to")

        if source_name and destination_name:
            queryset = queryset.filter(
                source__name__icontains=source_name,
                destination__name__icontains=destination_name
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "create":
            return RouteCreateSerializer
        elif self.action == "retrieve":
            return RouteDetailSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "from",
                type=str,
                description="Filtering by source (ex. ?from=Kansas)"
            ),
            OpenApiParameter(
                "to",
                type=str,
                description="Filtering by destination (ex. ?to=Nevada)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=str,
                description="Filtering by name (ex. ?name=Wide-Body)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type")
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        name = self.request.query_params.get("name")
        airplane_type = self.request.query_params.get("airplane_type")

        if name:
            queryset = queryset.filter(name__icontains=name)

        if airplane_type:
            queryset = queryset.filter(
                airplane_type__name__icontains=airplane_type
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        elif self.action == "create":
            return AirplaneCreateSerializer
        elif self.action == "retrieve":
            return AirplaneDetailSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=str,
                description="Filtering by name (ex. ?name=Boing)"
            ),
            OpenApiParameter(
                "airplane_type",
                type=str,
                description="Filtering by airplane_type (ex. ?airplane_type=Wide-Body)"
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.select_related(
        "route__source", "route__destination", "airplane"
    ).prefetch_related("crew")
    serializer_class = FlightListSerializer
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        current_time = timezone.now()

        flights = (
            queryset
            .filter(departure_time__gt=current_time)
            .annotate(
                available_tickets=F("airplane__rows") * F("airplane__seats_in_rows") - Count("tickets")
            )
        )

        from_ = self.request.query_params.get("from")
        to = self.request.query_params.get("to")
        departure = self.request.query_params.get("departure_time")
        arrival = self.request.query_params.get("arrival_time")

        if from_:
            flights = flights.filter(
                route__source__closest_big_city__icontains=from_
            )

        if to:
            flights = flights.filter(
                route__destination__closest_big_city__icontains=to
            )

        if departure:
            departure_datetime = datetime.strptime(departure, "%Y-%m-%dT%H:%M:%SZ")
            flights = flights.filter(departure_time=departure_datetime)

        if arrival:
            arrival_datetime = datetime.strptime(arrival, "%Y-%m-%dT%H:%M:%SZ")
            flights = flights.filter(arrival_time=arrival_datetime)

        return flights

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "create":
            return FlightCreateSerializer
        elif self.action == "retrieve":
            return FlightDetailSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "from",
                type=str,
                description="Filter flights by source city (ex. ?from=Kyiv)",
            ),
            OpenApiParameter(
                "to",
                type=str,
                description="Filter flights by destination city (ex. ?to=London)",
            ),
            OpenApiParameter(
                "departure_time",
                type=str,
                description="Filter flights by departure time (format: %Y-%m-%dT%H:%M:%SZ)",
            ),
            OpenApiParameter(
                "arrival_time",
                type=str,
                description="Filter flights by arrival time (format: %Y-%m-%dT%H:%M:%SZ)",
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = FlightCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("user").prefetch_related("tickets__flight")
    serializer_class = OrderListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "create":
            return OrderCreateSerializer
        elif self.action == "retrieve":
            return OrderDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
