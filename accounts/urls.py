from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('employees/', views.get_all_employees, name='get-all-employees'),
    path('employees/create/', views.create_employee, name='create-employee'),    
    path('employees/<int:pk>/', views.get_employee_detail, name='get-employee-detail'),
    path('employees/<int:pk>/update/', views.update_employee, name='update-employee'),
    path('employees/<int:pk>/delete/', views.delete_employee, name='delete-employee'),
]