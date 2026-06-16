from django.urls import path
from . import views

urlpatterns = [
    # Sites
    path('sites/', views.get_all_sites, name='get-all-sites'),
    path('sites/create/', views.create_site, name='create-site'),
    path('sites/<int:pk>/', views.get_site_detail, name='get-site-detail'),
    path('sites/<int:pk>/update/', views.update_site, name='update-site'),
    path('sites/<int:pk>/delete/', views.delete_site, name='delete-site'),
    path('sites/<int:pk>/assignments/', views.site_assignments, name='site-assignments'),
    # Assignments
    path('assignments/', views.get_all_assignments, name='get-all-assignments'),
    path('assignments/create/', views.create_assignment, name='create-assignment'),
    path('assignments/<int:pk>/update/', views.update_assignment, name='update-assignment'),
    path('assignments/<int:pk>/delete/', views.delete_assignment, name='delete-assignment'),
    # Employee self-service
    path('my-assignments/', views.my_assignments, name='my-assignments'),
]
