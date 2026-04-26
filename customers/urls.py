from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_all_customers, name='get-all-customers'),
    path('create/', views.create_customer, name='create-customer'),   
    path('<int:pk>/', views.get_customer_detail, name='get-customer-detail'),
    path('<int:pk>/update/', views.update_customer, name='update-customer'),
    path('<int:pk>/delete/', views.delete_customer, name='delete-customer'),
]