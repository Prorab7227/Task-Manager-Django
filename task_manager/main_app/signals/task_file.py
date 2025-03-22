from django.db.models.signals import pre_delete
from django.dispatch import receiver
from ..models import TaskFile
from django.core.exceptions import ValidationError
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from b2sdk._internal.exception import FileNotPresent

from django.conf import settings

@receiver(pre_delete, sender=TaskFile)
def delete_task_file_from_b2(sender, instance, **kwargs):
    if instance.file_path:
        try:
            # Инициализация B2 API
            info = InMemoryAccountInfo()
            b2_api = B2Api(info)
            
            APPLICATION_KEY_ID = settings.B2_APPLICATION_KEY_ID
            APPLICATION_KEY = settings.B2_APPLICATION_KEY

            b2_api.authorize_account("production", APPLICATION_KEY_ID, APPLICATION_KEY)
            
            print(instance.name)

            # Получение file_id и имени файла из пути
            file_id = instance.file_path.split('=')[-1]  # Или другой метод получения file_id
            
            # Получение информации о файле
            file_info = b2_api.get_file_info(file_id)
            file_name = file_info.file_name
            
            # Удаление файла из B2
            bucket = b2_api.get_bucket_by_id(file_info.bucket_id)
            bucket.delete_file_version(file_id, file_name)
            
            print(f"Delete successfull '{file_name}'.")
        except ValidationError:
            print(f"File not found in B2.")
        except FileNotPresent:
            print(f"File not found in B2.")
        except Exception as e:
            print(f"ERROR DELETING: {e}")
