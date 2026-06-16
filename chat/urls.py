from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # Conversations
    # ==========================================
    path('conversations/', views.get_my_conversations, name='my-conversations'),
    path('conversations/group/create/', views.create_group, name='create-group'),
    path('conversations/direct/create/', views.create_direct, name='create-direct'),
    path('conversations/<int:pk>/', views.get_conversation_detail, name='conversation-detail'),
    path('conversations/<int:pk>/add-members/', views.add_participants, name='add-members'),

    # ==========================================
    # Messages
    # ==========================================
    path('conversations/<int:pk>/messages/', views.get_messages, name='get-messages'),
    path('conversations/<int:pk>/messages/send/', views.send_message, name='send-message'),
]
