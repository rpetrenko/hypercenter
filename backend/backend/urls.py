from django.contrib import admin
from django.urls import path, include
from search import urls as search_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('search/', include(search_urls)),
]
