from django.contrib import admin
from .models import AutoTradeLog, AutoPosition


@admin.register(AutoTradeLog)
class AutoTradeLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'symbol', 'signal', 'action_taken', 'market_price')
    list_filter = ('signal', 'symbol', 'action_taken')
    search_fields = ('user__username', 'symbol')
    readonly_fields = ('created_at',)


@admin.register(AutoPosition)
class AutoPositionAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'user', 'quantity', 'entry_price', 'is_open', 'opened_at')
    list_filter = ('is_open', 'symbol')
