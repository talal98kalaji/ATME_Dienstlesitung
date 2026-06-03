from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # Project URLs (روابط المشاريع)
    # ==========================================
    path('', views.get_all_projects, name='get-all-projects'),
    path('create/', views.create_project, name='create-project'),
    path('<int:pk>/', views.get_project_detail, name='get-project-detail'),
    path('<int:pk>/update/', views.update_project, name='update-project'),
    path('<int:pk>/delete/', views.delete_project, name='delete-project'),

    # ==========================================
    # Task URLs (روابط مهام الخطة)
    # ==========================================
    path('tasks/create/', views.create_task, name='create-task'),
    path('tasks/<int:pk>/update-status/', views.update_task_status, name='update-task-status'),
    path('tasks/<int:pk>/delete/', views.delete_task, name='delete-task'),

    # ==========================================
    # Comment URLs (روابط التعليقات)
    # ==========================================
    # نمرر رقم المشروع (project_id) في الرابط لربط التعليق به مباشرة
    path('<int:project_id>/comments/add/', views.add_project_comment, name='add-project-comment'),
]