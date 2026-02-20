from django.contrib import admin
from .models import (
    Award,
    VideoAward,
    AwardVote,
)

# Register your models here.


class AwardAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Award, AwardAdmin)
admin.site.register(VideoAward)
admin.site.register(AwardVote)