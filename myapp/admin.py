from django.contrib import admin
from .models import Cashfree_Payment

@admin.register(Cashfree_Payment)
class CashfreePaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'amount', 'customer_id', 'status', 'created_at')
    search_fields = ('order_id', 'customer_id', 'status')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('order_id', 'created_at')

    # Optional: Make fields read-only after creation
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('amount', 'customer_id',)
        return self.readonly_fields
