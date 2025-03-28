from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Bouquet, Order


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'full_name', 'phone', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'full_name', 'phone')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'phone')}),
        (_('Permissions'), {'fields': ('role', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'full_name', 'phone', 'password1', 'password2', 'role', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'florist':
            return qs.defer('role')
        return qs

    def has_change_permission(self, request, obj=None):
        if request.user.role == 'florist':
            return False
        return super().has_change_permission(request, obj)

    def has_view_permission(self, request, obj=None):
        if request.user.role == 'florist':
            return True
        return super().has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'occasion', 'is_active', 'created_at')
    list_filter = ('occasion', 'is_active', 'price')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    fields = ('title', 'description', 'price', 'photo', 'occasion', 'is_active')

    def has_change_permission(self, request, obj=None):
        if request.user.role == 'florist':
            return False
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        if request.user.role == 'florist':
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'customer_name', 'phone', 'address', 'bouquet', 'status', 'florist', 'delivery_datetime', 'total_price', 'created_at')
    list_filter = ('status', 'delivery_datetime', 'florist')
    search_fields = ('customer_name', 'phone', 'address', 'user__username')
    ordering = ('-created_at',)
    fields = ('status', 'florist', 'delivery_datetime', 'total_price', 'bouquet', 'customer_name', 'phone', 'address')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'florist':
            return qs.filter(florist=request.user)
        return qs

    def has_change_permission(self, request, obj=None):
        if request.user.role == 'florist':
            if obj and obj.status in ('paid', 'delivered', 'canceled'):
                return False
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False
