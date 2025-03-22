from rest_framework import generics
from .models import Screenshot, Screener
# from .serializers import ScreenshotSerializer, ScreenerSerializer

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import os
from django.utils import timezone
import tempfile
from .views.backblaze import upload_to_backblaze  # Function for loading on Backblaze
    
class TempFileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Получаем список файлов из запроса
        files = request.FILES.getlist('file')
        uploaded_files = []

        for file in files:
            try:
                today = timezone.now().date()
                # Временный путь для файла (используем имя пользователя для изоляции)
                file_path = f"task_files/{today}/{request.user.username}/{file.name}"
                file_path = file_path.replace(" ", "")
                
                # Создаем временный файл для загрузки на Backblaze
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name.replace('\\', '/')
                
                # Загружаем файл на Backblaze
                file_id = upload_to_backblaze(temp_file_path, file_path)
                os.remove(temp_file_path)

                if file_id:
                    # Возвращаем информацию о загруженном файле
                    uploaded_files.append({
                        "name": file.name,
                        "size": file.size,
                        "url": f"https://f003.backblazeb2.com/b2api/v1/b2_download_file_by_id?fileId={file_id}",
                        "file_id": file_id
                    })
            
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"uploaded_files": uploaded_files}, status=status.HTTP_201_CREATED)

class TaskCommentFileUploadView(APIView):
    permission_classes = [IsAuthenticated]  # Only for authenticated users

    def post(self, request):
        # Получаем список файлов из запроса
        files = request.FILES.getlist('file')
        uploaded_files = []

        for file in files:
            try:
                today = timezone.now().date()
                # Временный путь для файла (используем имя пользователя для изоляции)
                file_path = f"task_comment_files/{today}/{request.user.username}/{file.name}"
                file_path = file_path.replace(" ", "")
                
                # Создаем временный файл для загрузки на Backblaze
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name.replace('\\', '/')
                
                # Загружаем файл на Backblaze
                file_id = upload_to_backblaze(temp_file_path, file_path)
                os.remove(temp_file_path)

                if file_id:
                    # Возвращаем информацию о загруженном файле
                    uploaded_files.append({
                        "name": file.name,
                        "size": file.size,
                        "url": f"https://f003.backblazeb2.com/b2api/v1/b2_download_file_by_id?fileId={file_id}",
                        "file_id": file_id
                    })
            
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"uploaded_files": uploaded_files}, status=status.HTTP_201_CREATED)

class ProjectCommentFileUploadView(APIView):
    permission_classes = [IsAuthenticated]  # Only for authenticated users

    def post(self, request):
        # Получаем список файлов из запроса
        files = request.FILES.getlist('file')
        uploaded_files = []

        for file in files:
            try:
                today = timezone.now().date()
                # Временный путь для файла (используем имя пользователя для изоляции)
                file_path = f"project_comment_files/{today}/{request.user.username}/{file.name}"
                file_path = file_path.replace(" ", "")
                
                # Создаем временный файл для загрузки на Backblaze
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name.replace('\\', '/')
                
                # Загружаем файл на Backblaze
                file_id = upload_to_backblaze(temp_file_path, file_path)
                os.remove(temp_file_path)

                if file_id:
                    # Возвращаем информацию о загруженном файле
                    uploaded_files.append({
                        "name": file.name,
                        "size": file.size,
                        "url": f"https://f003.backblazeb2.com/b2api/v1/b2_download_file_by_id?fileId={file_id}",
                        "file_id": file_id
                    })
            
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"uploaded_files": uploaded_files}, status=status.HTTP_201_CREATED)
    
class ProjectReportFileUploadView(APIView):
    permission_classes = [IsAuthenticated]  # Only for authenticated users

    def post(self, request):
        # Получаем список файлов из запроса
        files = request.FILES.getlist('file')
        uploaded_files = []

        for file in files:
            try:
                today = timezone.now().date()
                # Временный путь для файла (используем имя пользователя для изоляции)
                file_path = f"project_reports_files/{today}/{request.user.username}/{file.name}"
                file_path = file_path.replace(" ", "")
                
                # Создаем временный файл для загрузки на Backblaze
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name.replace('\\', '/')
                
                # Загружаем файл на Backblaze
                file_id = upload_to_backblaze(temp_file_path, file_path)
                os.remove(temp_file_path)

                if file_id:
                    # Возвращаем информацию о загруженном файле
                    uploaded_files.append({
                        "name": file.name,
                        "size": file.size,
                        "url": f"https://f003.backblazeb2.com/b2api/v1/b2_download_file_by_id?fileId={file_id}",
                        "file_id": file_id
                    })
            
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"uploaded_files": uploaded_files}, status=status.HTTP_201_CREATED)

from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
@api_view(['POST'])
def get_session_token(request):
    if request.user.is_authenticated:
        token, created = Token.objects.get_or_create(user=request.user)
        return Response({'key': token.key})
    return Response({'error': 'User is not found'}, status=401)


# class ScreenshotCreateView(generics.CreateAPIView):
#     queryset = Screenshot.objects.all()
#     serializer_class = ScreenshotSerializer
#     permission_classes = [IsAuthenticated]

# class ScreenerCreateView(generics.CreateAPIView):
#     queryset = Screener.objects.all()
#     serializer_class = ScreenerSerializer
#     permission_classes = [IsAuthenticated]

class TokenValidationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Token is valid!"}, status=status.HTTP_200_OK)