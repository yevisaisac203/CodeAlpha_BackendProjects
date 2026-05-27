import django_filters

from .models import Event


class EventFilter(django_filters.FilterSet):
    is_free = django_filters.BooleanFilter(method="filter_is_free")
    date_from = django_filters.DateFilter(field_name="start_datetime", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="start_datetime", lookup_expr="lte")
    min_price = django_filters.NumberFilter(field_name="ticket_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="ticket_price", lookup_expr="lte")

    class Meta:
        model = Event
        fields = ["category", "city", "is_virtual", "is_free", "status"]

    def filter_is_free(self, queryset, name, value):
        if value is True:
            return queryset.filter(ticket_price=0)
        if value is False:
            return queryset.exclude(ticket_price=0)
        return queryset
