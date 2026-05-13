from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_expense, name='add_expense'),
    path('delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]