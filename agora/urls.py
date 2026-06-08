from django.urls import path, register_converter
from . import views
from .converters import Base36Converter

register_converter(Base36Converter, 'b36')

urlpatterns = [
    path('', views.agora, name='agora'),
    path('thread/<b36:pk>/', views.agora_thread, name='agora_thread'),
    path('boards/search/', views.agora_board_search, name='agora_board_search'),
    path('boards/follow/', views.toggle_follow_board, name='agora_toggle_follow_board'),
    path('post/<b36:post_id>/edit/', views.agora_edit_post, name='agora_edit_post'),
    path('post/<b36:post_id>/delete/', views.agora_delete_post, name='agora_delete_post'),
    path('post/<b36:post_id>/reply/', views.agora_create_reply, name='agora_create_reply'),
    path('<b36:board_id>/post/', views.agora_create_post, name='agora_create_post'),
    path('<b36:board_id>/', views.agora, name='agora_board'),
]
