from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, EventViewSet, RegistrationViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("events", EventViewSet, basename="event")
router.register("registrations", RegistrationViewSet, basename="registration")

urlpatterns = router.urls
