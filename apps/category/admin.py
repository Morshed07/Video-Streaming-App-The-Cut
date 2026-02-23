from django.contrib import admin
from .models import Category, Tag

# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'audience_type', 'is_active', 'created_at')
    search_fields = ('name', 'audience_type')
    list_filter = ('is_active', 'audience_type', 'created_at')
    ordering = ('name',)
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag)