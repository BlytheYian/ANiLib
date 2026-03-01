from django.urls import path
from . import views

urlpatterns = [
    # 這裡可以暫時留空，或者放你原本定義的內容
    path('<int:pk>/', views.ani_detail, name='ani_detail'),
    path('', views.ani_lib, name='ani_lib'),
]