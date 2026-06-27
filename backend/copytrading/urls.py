from django.urls import path

from . import views

app_name = "copytrading"

urlpatterns = [
    path("", views.traders, name="traders"),
    path("copy/<slug:slug>/", views.copy, name="copy"),
    path("mine/", views.my_copies, name="my_copies"),
    path("stop/<int:pk>/", views.stop, name="stop"),
]
