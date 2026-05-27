from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .filters import EventFilter
from .models import Category, Event, Registration
from .permissions import IsEventOwner, IsOrganizer
from .serializers import (
    CategorySerializer,
    EventCreateUpdateSerializer,
    EventDetailSerializer,
    EventListSerializer,
    RegistrationCreateSerializer,
    RegistrationSerializer,
)
from .signals import promote_from_waitlist


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

    @action(detail=True, methods=["post"], url_path="register")
    def register(self, request, slug=None):
        event = get_object_or_404(
            Event.objects.select_related("category", "organizer"),
            slug=slug,
        )
        if event.status != Event.STATUS_PUBLISHED:
            return Response(
                {"error": "This event is not open for registration."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = Registration.objects.filter(
            user=request.user, event=event
        ).exclude(status=Registration.STATUS_CANCELLED)
        if existing.exists():
            return Response(
                {"error": "You already have an active registration for this event."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration_status = (
            Registration.STATUS_WAITLISTED if event.is_full else Registration.STATUS_CONFIRMED
        )
        serializer = RegistrationCreateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        registration = serializer.save(
            user=request.user,
            event=event,
            status=registration_status,
        )
        return Response(
            RegistrationSerializer(registration, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path="unregister")
    def unregister(self, request, slug=None):
        event = get_object_or_404(Event, slug=slug)
        registration = Registration.objects.filter(
            user=request.user,
            event=event,
        ).exclude(status=Registration.STATUS_CANCELLED).first()

        if not registration:
            return Response({"error": "Registration not found."}, status=status.HTTP_404_NOT_FOUND)

        registration.status = Registration.STATUS_CANCELLED
        registration.save(update_fields=["status"])
        promote_from_waitlist(event)
        return Response({"message": "Registration cancelled"}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path="attendees",
        permission_classes=[IsAuthenticated, IsEventOwner],
    )
    def attendees(self, request, slug=None):
        event = self.get_object()
        registrations = event.registrations.filter(
            status=Registration.STATUS_CONFIRMED
        ).select_related("event", "event__category", "event__organizer")
        serializer = RegistrationSerializer(registrations, many=True, context={"request": request})
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        url_path="stats",
        permission_classes=[IsAuthenticated, IsEventOwner],
    )
    def stats(self, request, slug=None):
        event = self.get_object()
        registrations = event.registrations.all()
        data = {
            "confirmed_count": registrations.filter(status=Registration.STATUS_CONFIRMED).count(),
            "waitlisted_count": registrations.filter(status=Registration.STATUS_WAITLISTED).count(),
            "cancelled_count": registrations.filter(status=Registration.STATUS_CANCELLED).count(),
            "checked_in_count": registrations.exclude(check_in_time__isnull=True).count(),
            "available_spots": event.available_spots,
            "event_title": event.title,
        }
        return Response(data)


class RegistrationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        queryset = Registration.objects.select_related(
            "event", "event__category", "event__organizer"
        )
        user = self.request.user
        if user.role == "admin":
            return queryset.order_by("-registered_at")
        return queryset.filter(user=user).order_by("-registered_at")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RegistrationCreateSerializer
        return RegistrationSerializer

    @action(detail=False, methods=["get"], url_path="mine")
    def my_registrations(self, request):
        queryset = Registration.objects.filter(user=request.user).select_related(
            "event", "event__category", "event__organizer"
        ).order_by("-registered_at")
        serializer = RegistrationSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path=r"ticket/(?P<ticket_code>[^/.]+)")
    def by_ticket(self, request, ticket_code=None):
        registration = get_object_or_404(
            Registration.objects.select_related("event", "event__category", "event__organizer"),
            ticket_code=ticket_code,
        )
        if registration.user != request.user and registration.event.organizer != request.user:
            return Response({"error": "You do not have permission to view this ticket."}, status=403)
        serializer = RegistrationSerializer(registration, context={"request": request})
        return Response(serializer.data)
