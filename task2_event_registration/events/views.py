from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import EventFilter
from .models import Category, Event
from .permissions import IsEventOwner, IsOrganizer
from .serializers import (
    CategorySerializer,
    EventCreateUpdateSerializer,
    EventDetailSerializer,
    EventListSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class EventViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"
    filterset_class = EventFilter
    search_fields = ["title", "description", "city", "organizer__username"]
    ordering_fields = ["start_datetime", "created_at", "ticket_price"]

    def get_queryset(self):
        base_qs = Event.objects.select_related("category", "organizer")
        queryset = base_qs.filter(status=Event.STATUS_PUBLISHED)

        user = self.request.user
        if user.is_authenticated and user.role in ["organizer", "admin"]:
            queryset = base_qs.filter(
                Q(status=Event.STATUS_PUBLISHED)
                | Q(status=Event.STATUS_DRAFT, organizer=user)
            )

        return queryset.order_by("start_datetime").distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return EventListSerializer
        if self.action == "retrieve":
            return EventDetailSerializer
        return EventCreateUpdateSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "upcoming"]:
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated(), IsOrganizer()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsEventOwner()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming(self, request):
        upcoming_events = (
            Event.objects.select_related("category", "organizer")
            .filter(status=Event.STATUS_PUBLISHED)
            .order_by("start_datetime")[:10]
        )
        serializer = EventListSerializer(upcoming_events, many=True, context={"request": request})
        return Response(serializer.data)
