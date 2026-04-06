from django.contrib import admin
from .models import Video, WatchHistory

# Register your models here.


class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'upload_by', 'category', 'age_rating', 'created_at')
    search_fields = ('title', 'description', 'upload_by__username', 'category__name')
    list_filter = ('age_rating', 'category', 'created_at')
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('title',)}


class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'watch_duration', 'last_watched_at')
    search_fields = ('user__username', 'video__title')
    list_filter = ('last_watched_at',)
    ordering = ('-last_watched_at',)


admin.site.register(Video, VideoAdmin)
admin.site.register(WatchHistory, WatchHistoryAdmin)