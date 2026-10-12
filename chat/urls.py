from django.urls import path

from . import views


urlpatterns = [
    path("conversations/", views.get_my_conversations, name="my-conversations",),
    path("conversations/group/create/", views.create_group, name="create-group",),
    path("conversations/direct/create/", views.create_direct, name="create-direct",),
    path("conversations/<int:pk>/", views.get_conversation_detail, name="conversation-detail",),
    path("conversations/<int:pk>/settings/", views.group_settings, name="chat-group-settings",),
    path("conversations/<int:pk>/add-members/", views.add_participants, name="add-members",),
    path("conversations/<int:pk>/members/<int:user_id>/", views.member_detail, name="chat-member-detail",),
    path("conversations/<int:pk>/messages/", views.get_messages, name="get-messages",),
    path("conversations/<int:pk>/messages/send/",views.send_message,name="send-message",),
    path("conversations/<int:pk>/pins/",views.get_pinned_messages,name="chat-pins",),
    path("conversations/<int:pk>/messages/<int:message_id>/pin/",views.message_pin,name="chat-message-pin",),
    path("conversations/<int:pk>/messages/<int:message_id>/image/",views.message_image,name="chat-message-image",),
]