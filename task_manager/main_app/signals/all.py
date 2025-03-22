from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from ..models import Folder, Project, Tag

@receiver(post_migrate)
def create_generals(sender, **kwargs):
    User = get_user_model()

    # Создаем суперпользователя, если его нет
    if not User.objects.filter(username="ADMIN").exists():
        User.objects.create_superuser(username="ADMIN", password="admin12345")

    # Получаем первого суперпользователя
    owner = User.objects.filter(is_superuser=True).order_by("id").first()

    if not Folder.objects.filter(name="General").exists():
        Folder.objects.create(name="General", slug="general", owner=owner)

    if not Tag.objects.filter(name="General").exists():
        Tag.objects.create(name="General", slug="general", author=owner)

    if not Project.objects.filter(name="General").exists():
        general_tag = Tag.objects.filter(name="General").first()
        Project.objects.create(name="General", slug="general", owner=owner, tag=general_tag)
