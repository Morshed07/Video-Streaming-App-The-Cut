from django.contrib import admin
from .models import Category

# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'slug')
    list_filter = ('is_active', 'created_at', 'updated_at')
    ordering = ('name',)
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Category, CategoryAdmin)
