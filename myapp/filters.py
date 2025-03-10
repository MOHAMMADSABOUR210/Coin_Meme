from .models import Transaction
import django_filters


class TransactionFilter(django_filters.FilterSet):
    start_date = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    end_date = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")
    min_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    transaction_type = django_filters.CharFilter(field_name="transaction_type", lookup_expr="iexact")
    sender = django_filters.CharFilter(field_name="sender__user__username", lookup_expr="icontains")
    receiver = django_filters.CharFilter(field_name="receiver__user__username", lookup_expr="icontains")

    class Meta:
        model = Transaction
        fields = ['start_date', 'end_date', 'min_amount', 'max_amount', 'transaction_type', 'sender', 'receiver']
