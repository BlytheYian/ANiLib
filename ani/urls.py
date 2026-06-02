from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.ani_detail, name='ani_detail'),
    path('<int:pk>/review/', views.submit_review, name='submit_review'),
    path('', views.ani_lib, name='ani_lib'),
]