from django.urls import path

from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.feed, name='feed'),
    path('submit/', views.submit, name='submit'),
    path('mine/', views.my_posts, name='my_posts'),
]
