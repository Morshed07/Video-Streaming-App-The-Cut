from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/users/', include('apps.user.urls')),
    path('api/categories/', include('apps.category.urls')),
    path('api/awards/', include('apps.award.urls')),
    path('api/videos/', include('apps.video.urls')),
    path('api/reviews/', include('apps.review.urls')),
    path('api/notifications/', include('apps.notification.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
