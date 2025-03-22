import json
from django.contrib.auth import authenticate, get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token
from datetime import datetime, timedelta
from main_app.models import Screener, Screenshot
import os
from django.utils.timezone import now
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
import base64

User = get_user_model()

class AuthConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        username = data.get("username")
        password = data.get("password")

        # Аутентификация пользователя
        user = await sync_to_async(authenticate)(username=username, password=password)

        if user:
            token, _ = await sync_to_async(Token.objects.get_or_create)(user=user)
            response = {"message": "success", "token": token.key}
        else:
            response = {"message": "error"}

        await self.send(json.dumps(response))

    async def disconnect(self, close_code):
        pass

import asyncio
class ScreenerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = None
        self.screener = None
        self.running = True
        await self.accept()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            token = data.get("token")
            if not token:
                await self.send(json.dumps({"error": "Token is required"}, ensure_ascii=False))
                return

            token_obj = await sync_to_async(Token.objects.get, thread_sensitive=True)(key=token)
            self.user = await sync_to_async(lambda: token_obj.user, thread_sensitive=True)()
            today = datetime.now().date()
            self.screener, _ = await sync_to_async(Screener.objects.get_or_create, thread_sensitive=True)(
                user=self.user, date=today
            )

            asyncio.create_task(self.track_time())
        except json.JSONDecodeError:
            await self.send(json.dumps({"error": "Invalid JSON format"}, ensure_ascii=False))
        except Token.DoesNotExist:
            await self.send(json.dumps({"error": "Invalid token"}, ensure_ascii=False))
        except Exception as e:
            await self.send(json.dumps({"error": str(e)}, ensure_ascii=False))

    async def track_time(self):
        while self.running:
            await asyncio.sleep(1)
            self.screener.work_time += timedelta(seconds=1)
            await sync_to_async(self.screener.save, thread_sensitive=True)()
            response = {
                "id": self.screener.id,
                "work_time": str(self.screener.work_time),
                "username": self.user.username,
                "date": str(self.screener.date),
                "status": "updated"
            }
            await self.send(json.dumps(response, ensure_ascii=False))

    async def disconnect(self, close_code):
        self.running = False

class ScreenshotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        try:
            # Загружаем JSON из входящего WebSocket-сообщения
            data = json.loads(text_data)

            token = data.get("token")
            image_name = data.get("image_name")
            image_data = data.get("image_base64")  # Получаем данные изображения (base64)

            if not token or not image_data:
                await self.send(json.dumps({"error": "Missing required fields (token, image)"}, ensure_ascii=False))
                return

            # Получаем пользователя по токену
            token_obj = await sync_to_async(Token.objects.get, thread_sensitive=True)(key=token)
            user = await sync_to_async(lambda: token_obj.user, thread_sensitive=True)()

            # Определяем текущую дату
            today = now().date()

            # Получаем или создаем Screener для текущего пользователя и даты
            screener, created = await sync_to_async(Screener.objects.get_or_create, thread_sensitive=True)(
                user=user,
                date=today
            )

            # Декодируем изображение из base64
            try:
                # base64 строка
                image_data = image_data.split(",")[1]  # Убираем начало строки base64
                image_bytes = base64.b64decode(image_data)

                image_file = InMemoryUploadedFile(
                    BytesIO(image_bytes), None, image_name, 'image/webp', len(image_bytes), None
                )

            except Exception as e:
                await self.send(json.dumps({"error": f"Error decoding image data: {e}"}, ensure_ascii=False))
                return

            # Создаем объект Screenshot
            screenshot = await sync_to_async(Screenshot.objects.create, thread_sensitive=True)(
                user=user, screener=screener, image=image_file
            )

            # Парсим дату и время из имени файла
            image_filename = os.path.basename(screenshot.image.name)
            try:
                # Пример: Screenshot_20250212_101336.WEBP
                filename_parts = image_filename.split('_')
                date_str = filename_parts[1]
                time_str = filename_parts[2].replace('.webp', '')  # Убираем расширение

                # Конвертируем в формат datetime
                screenshot_created_time = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')

                # Сохраняем дату создания
                screenshot.created = screenshot_created_time

            except Exception as e:
                # Ошибка при парсинге, ставим текущее время
                await self.send(json.dumps({"error": f"Error parsing datetime from filename: {e}"}, ensure_ascii=False))

            await sync_to_async(screenshot.save, thread_sensitive=True)()

            # Отправляем подтверждение
            response = {
                "id": screenshot.id,
                "screener": screener.id,
                "username": user.username,
                "image": screenshot.image.url,
                "created": str(screenshot.created),
                "status": "saved"
            }
            await self.send(json.dumps(response, ensure_ascii=False))

        except json.JSONDecodeError:
            await self.send(json.dumps({"error": "Invalid JSON format"}, ensure_ascii=False))
        except Token.DoesNotExist:
            await self.send(json.dumps({"error": "Invalid token"}, ensure_ascii=False))
        except Exception as e:
            await self.send(json.dumps({"error": str(e)}, ensure_ascii=False))

    async def disconnect(self, close_code):
        pass