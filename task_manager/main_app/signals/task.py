from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.core.serializers import serialize

from ..models import Folder, Project, Task, Action


import threading
# Создаем локальный объект для хранения информации о текущем пользователе
_thread_locals = threading.local()
def set_current_user(user):
    _thread_locals.user = user
def get_current_user():
    return getattr(_thread_locals, 'user', None)

def serialize_instance(instance):
    """Функция для сериализации всех полей объекта в строку."""
    # Возвращаем первый элемент из сериализованного списка, а не весь список
    return serialize('json', [instance])  # Возвращаем строку, а не список

def save_action(instance, action_type, context_before=None, context_after=None):
    """Сохраняем экшен после создания или обновления объекта."""
    user = get_current_user()
    Action.objects.create(
        author=user,
        task=instance if isinstance(instance, Task) else None,
        project=instance if isinstance(instance, Project) else None,
        folder=instance if isinstance(instance, Folder) else None,
        action_type=action_type,
        context_before=context_before,  # Save the context to
        context_after=context_after  # maintain the context after
    )

@receiver(pre_save, sender=Task)
def pre_save_action(sender, instance, **kwargs):
    """Processing the object before maintaining it (we get the old version of the object)."""
    print(sender)
    print(instance)
    print(kwargs)
    if not instance.pk:  # If this is a new object, we miss processing
        return
    
    # We get an old version of the object before changing
    instance_before_update = sender.objects.get(pk=instance.pk)
    context_before = serialize_instance(instance_before_update)

    # Save the context to update
    instance._context_before = context_before

@receiver(post_save, sender=Task)
def post_save_action(sender, instance, created, **kwargs):
    """The processing of the object after its preservation (serialization of a new state)."""
    action_type = 'create' if created else 'update'
    
    # Serialize the object after changing
    context_after = serialize_instance(instance)
    
    # We get the context to change from pre_save
    context_before = getattr(instance, '_context_before', None)
    
    # Save the action
    save_action(instance, action_type, context_before, context_after)

@receiver(pre_delete, sender=Task)
def delete_action(sender, instance, **kwargs):
    """Обработка объекта перед его удалением."""
    try:
        context_before = serialize_instance(instance)
        
        user = get_current_user()  # We get the current user

        # We create an entry on deletion in the Journal of Actions
        Action.objects.create(
            author=user,
            task=instance,
            action_type='delete',
            context_before=context_before,  # Context before removal
            context_after=None  # There is no context after removal
        )
    except Exception as e:
        print(f"Ошибка при создании Action: {e}")
        raise  # Repeated exception to diagnosis