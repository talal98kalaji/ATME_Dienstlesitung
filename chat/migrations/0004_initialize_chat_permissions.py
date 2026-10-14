from django.db import migrations
from django.db.models import Q


def initialize_groups(apps, schema_editor):
    Conversation = apps.get_model("chat", "Conversation")
    Participant = apps.get_model("chat", "Participant")
    User = apps.get_model("accounts", "CustomUser")

    database = schema_editor.connection.alias

    users = User.objects.using(database)

    leaders = users.filter(is_active=True).filter(
        Q(is_superuser=True)
        | Q(user_type="MANAGER")
        | (
            Q(level="SENIOR")
            & ~Q(user_type__in=["DATA_ENTRY", "MANAGER"])
        )
    )

    fallback = (
        users.filter(is_active=True)
        .filter(
            Q(is_superuser=True)
            | Q(user_type="MANAGER")
        )
        .order_by("-is_superuser", "pk")
        .first()
    )

    groups = (
        Conversation.objects.using(database)
        .filter(conversation_type="GROUP")
    )

    for conversation in groups.iterator():
        owner = leaders.filter(
            pk=conversation.created_by_id
        ).first()

        if owner is None:
            member_ids = (
                Participant.objects.using(database)
                .filter(conversation_id=conversation.pk)
                .values_list("user_id", flat=True)
            )

            owner = (
                leaders.filter(pk__in=member_ids)
                .order_by("-is_superuser", "pk")
                .first()
            )

        if owner is None:
            owner = fallback

        if owner is None:
            raise RuntimeError(
                "Create an active Superuser, then rerun migrate."
            )

        conversation.managed_by_id = owner.pk
        conversation.send_policy = "ADMIN_ONLY"

        if owner.is_superuser or owner.user_type == "MANAGER":
            conversation.allowed_levels = [
                "JUNIOR",
                "MID",
                "SENIOR",
            ]
        else:
            conversation.allowed_levels = [
                "JUNIOR",
                "MID",
            ]

        conversation.save(
            using=database,
            update_fields=[
                "managed_by",
                "send_policy",
                "allowed_levels",
            ],
        )

        memberships = (
            Participant.objects.using(database)
            .filter(conversation_id=conversation.pk)
        )

        memberships.update(
            role="MEMBER",
            can_send_messages=False,
            can_add_members=False,
        )

        Participant.objects.using(database).get_or_create(
            conversation_id=conversation.pk,
            user_id=owner.pk,
            defaults={
                "added_by_id": owner.pk,
            },
        )

        memberships.filter(user_id=owner.pk).update(
            role="ADMIN",
            can_send_messages=True,
            can_add_members=True,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0003_chat_permissions"),
    ]

    operations = [
        migrations.RunPython(
            initialize_groups,
            migrations.RunPython.noop,
        ),
    ]