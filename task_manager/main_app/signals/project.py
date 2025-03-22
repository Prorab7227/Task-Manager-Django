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
        context_before=context_before,  # сохраняем контекст до
        context_after=context_after  # сохраняем контекст после
    )

@receiver(pre_save, sender=Project)
def pre_save_action(sender, instance, **kwargs):
    """Обработка объекта перед его сохранением (получаем старую версию объекта)."""
    if not instance.pk:  # Если это новый объект, пропускаем обработку
        return
    
    # Получаем старую версию объекта перед изменением
    instance_before_update = sender.objects.get(pk=instance.pk)
    context_before = serialize_instance(instance_before_update)
    
    # Сохраняем контекст до обновления
    instance._context_before = context_before

@receiver(post_save, sender=Project)
def post_save_action(sender, instance, created, **kwargs):
    """Обработка объекта после его сохранения (сериализация нового состояния)."""
    action_type = 'create' if created else 'update'
    
    # Сериализуем объект после изменения
    context_after = serialize_instance(instance)
    
    # Получаем контекст до изменения из pre_save
    context_before = getattr(instance, '_context_before', None)
    
    # Сохраняем экшен
    save_action(instance, action_type, context_before, context_after)

@receiver(pre_delete, sender=Project)
def delete_action(sender, instance, **kwargs):
    try:
        with transaction.atomic():
            context_before = serialize_instance(instance)
            
            user = get_current_user()

            action = Action.objects.create(
                author=user,
                task=instance if isinstance(instance, Task) else None,
                project=instance if isinstance(instance, Project) else None,
                folder=instance if isinstance(instance, Folder) else None,
                action_type='delete',
                context_before=context_before,  
                context_after=None 
            )
    except Exception as e:
        print(f"Ошибка при создании Action: {e}")
        raise  # Повторное выбрасывание исключения для диагностики