from django.contrib import admin
from .models import Category, Bouquet, User, Order, ConsultationRequest

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'telegram_id', 'name', 'phone')
    search_fields = ('name', 'telegram_id')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'bouquet', 'total_price', 'status', 'created_at')
    search_fields = ('user__name', 'bouquet__name')
    list_filter = ('status', 'created_at')

@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'processed')
    search_fields = ('user__name',)
    list_filter = ('processed', 'created_at')
