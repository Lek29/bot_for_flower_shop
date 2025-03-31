from django.contrib import admin
from django.utils.html import mark_safe
from .models import Bouquet  


@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'occasion', 'is_active', 'created_at', 'preview')
    list_filter = ('occasion', 'is_active', 'price')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    fields = ('title', 'description', 'price', 'photo', 'occasion', 'is_active', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="100" height="100" style="object-fit: cover;" />')
        return "Нет изображения"

    preview.short_description = 'Фото'
