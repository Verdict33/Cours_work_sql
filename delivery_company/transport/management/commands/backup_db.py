import os
import time
import subprocess
import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Создает резервную копию БД и загружает на Яндекс.Диск'

    def handle(self, *args, **options):
        db_conf = settings.DATABASES['default']

        timestamp = time.strftime('%Y-%m-%d_%H-%M')
        filename = f"backup_{timestamp}.sql"

        backup_dir = settings.BACKUP_DIR
        backup_dir.mkdir(exist_ok=True)

        filepath = backup_dir / filename

        self.stdout.write(f"Начало создания бэкапа: {filename}")

        env = os.environ.copy()
        env['PGPASSWORD'] = db_conf['PASSWORD']

        pg_dump_cmd = [
            'pg_dump',
            '-h', db_conf['HOST'],
            '-p', db_conf['PORT'],
            '-U', db_conf['USER'],
            '-F', 'p',
            '-f', str(filepath),
            db_conf['NAME']
        ]

        try:
            subprocess.run(pg_dump_cmd, env=env, check=True)
            self.stdout.write(self.style.SUCCESS(f"Дамп создан локально: {filepath}"))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при создании дампа: {e}"))
            return
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                "Ошибка: команда pg_dump не найдена. Убедитесь, что PostgreSQL добавлен в PATH или укажите полный путь к exe-файлу в скрипте."))
            return

        self.stdout.write("Загрузка в облако...")

        try:
            upload_url = self.get_upload_link(filename)
            with open(filepath, 'rb') as f:
                requests.put(upload_url, files={'file': f})

            self.stdout.write(self.style.SUCCESS(f"Файл успешно загружен на Яндекс.Диск: {filename}"))

            os.remove(filepath)
            self.stdout.write("Локальный файл удален.")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при загрузке в облако: {e}"))

    def get_upload_link(self, filename):
        headers = {'Authorization': f'OAuth {settings.YANDEX_DISK_TOKEN}'}
        params = {'path': f'/{filename}', 'overwrite': 'true'}

        response = requests.get(
            'https://cloud-api.yandex.net/v1/disk/resources/upload',
            headers=headers,
            params=params
        )
        if response.status_code != 200:
            raise Exception(f"Ошибка API Яндекса: {response.status_code} {response.text}")

        return response.json()['href']