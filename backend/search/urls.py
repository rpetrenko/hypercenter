from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from search.viewsets.hypermanager import HyperManagerDocumentView


router = DefaultRouter()
router.register(r'hypermanager',
                HyperManagerDocumentView,
                basename='hypermanager')


urlpatterns = [
    url(r'^', include(router.urls))
]