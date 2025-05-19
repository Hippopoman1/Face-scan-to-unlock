from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, FaceEncodingViewSet, GroupViewSet, UserGroupViewSet, 
    DeviceViewSet, AccessControlViewSet, AccessLogViewSet ,UploadFaceView ,UpdateFaceView
)


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'face-encodings', FaceEncodingViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'user-groups', UserGroupViewSet)
router.register(r'devices', DeviceViewSet)
router.register(r'access-controls', AccessControlViewSet)
router.register(r'access-logs', AccessLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', UploadFaceView.as_view(), name='upload_face'),
    path('update/', UpdateFaceView.as_view(), name='update-face'),
    
]
