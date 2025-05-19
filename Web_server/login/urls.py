from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', login, name='login'),
    path('login/', login, name='login'),
    path('home/', Home_view, name='home'),
    path('logout/', logout_views, name='logout'),
    path('profile/', profile, name='profile'),  # เส้นทางสำหรับหน้าโปรไฟล์

    path('door/', door_view, name='door'),
    path('add_door/', add_doors, name='add_door'),
    path('door/delete/<int:device_id>/', delete_door, name='delete_door'),
    path('door/add_user_to_door/<int:device_id>/', add_users_to_door, name='add_user_to_door'),
    # path('door/<int:device_id>/add-users/', add_users_to_door ,name='add_users_to_door'),
    path('delete_user_to_door/<int:device_id>',delete_user_to_door,name='delete_user_to_door'),
    
    path('add_admin/',add_admin,name='add_admin'),
    path('admin_view/', admin_view, name='admin'),

    path('log/', log_view, name='log'),
    path('log/search/', search.as_view(), name='search'),

    path('group/', group_view, name='group'),
    path('add_group/',add_group,name='add_group'),
    path('group/delete/<int:group_id>/', delete_group, name='delete_group'),
    path('group/edit/<int:pk>',edit_group.as_view(),name='edit_group'),
    path('group/add_user_to_group/<int:group_id>/',add_users_to_group, name='add_user_to_group'),
    path('group/<int:group_id>/add-users/', add_users_to_group, name='add_users_to_group'),

    
    
    path('user/',user_view,name='user'),
    path('add_user/',add_user,name='add_user'),
    path('upload_users/',upload_users,name='upload_users'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
