from django.urls import path

from . import views

app_name = 'education'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('<slug:slug>/', views.course_detail, name='course_detail'),
    path('<slug:slug>/enroll/', views.enroll, name='enroll'),
    path('<slug:slug>/lesson/<int:lesson_id>/', views.lesson_player, name='lesson'),
]
