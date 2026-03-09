from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.ani_detail, name='ani_detail'),
    path('', views.ani_lib, name='ani_lib'),
]