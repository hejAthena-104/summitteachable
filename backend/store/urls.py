from django.urls import path

from . import views

app_name = 'store'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('<slug:slug>/', views.checkout, name='checkout'),
]
