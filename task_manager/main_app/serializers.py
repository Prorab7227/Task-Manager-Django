from rest_framework import serializers
from .models import (Screenshot, Screener,
                    TaskFile, TaskCommentFile
                    )

from datetime import datetime  


class TaskFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskFile
        fields = ['name', 'task', 'author', 'file_path', 'size', 'uploaded_at']


class TaskCommentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCommentFile
        fields = ['name', 'task_comment', 'author', 'file_path', 'size', 'uploaded_at']


# class ScreenshotSerializer(serializers.ModelSerializer):
#     username = serializers.CharField(source='user.username', read_only=True)

#     class Meta:
#         model = Screenshot
#         fields = ['id', 'screener', 'username', 'image', 'created']

#     def create(self, validated_data):
#         user = self.context['request'].user
#         screenshot = Screenshot.objects.create(user=user, **validated_data)

#         # File name
#         image_filename = screenshot.image.name
#         image_filename = image_filename.split('/')[-1]
#         print(image_filename)
    
#         # Example dates and time from file name
#         try:
#             # File Name: Screenshot_20250212_101336.WEBP
#             filename_parts = image_filename.split('_')
#             date_str = filename_parts[1]
#             print(date_str)
#             time_str = filename_parts[2].replace('.webp', '')  # Убираем расширение
#             print(time_str)

#             # We convert a line into a DateTime format
#             screenshot_created_time = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')

#             # Set the date and time
#             screenshot.created = screenshot_created_time
#             print(screenshot_created_time)

#         except Exception as e:
#             # If something went wrong with the extraction, we will process the error
#             print(f"Error when extracting time from file name: {e}")
#            # screenshot.created = timezone.now()

#         screenshot.save()
#         return screenshot

# class ScreenerSerializer(serializers.ModelSerializer):
#     username = serializers.CharField(source='user.username', read_only=True)
#     status = serializers.CharField(read_only=True)

#     class Meta:
#         model = Screener
#         fields = ['id', 'work_time', 'username', 'status']

#     def create(self, validated_data):
#         user = self.context['request'].user
#         today = datetime.now().date()

#         screener, created = Screener.objects.get_or_create(
#             user=user,
#             date=today
#         )

#         screener.work_time = validated_data.get('work_time', screener.work_time)
#         screener.save()

#         screener.status = 'created' if created else 'updated'
        
#         return screener