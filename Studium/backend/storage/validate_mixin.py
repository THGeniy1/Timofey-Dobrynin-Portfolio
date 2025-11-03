import os
import re
import magic
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


class SimpleFileValidationMixin:


    allowed_extensions = {
        '.pdf', '.docx', '.doc', '.docm', '.xlsx', '.xls', '.xlsm', '.pptx', '.ppt', '.pptm',
        '.jpg', '.jpeg', '.png',
        '.zip', '.rar',
        '.txt'
    }
    dangerous_extensions = {'.exe', '.dll', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.hta', '.scr', '.pif', '.reg'}
                    
    allowed_mime_types = {

        'application/pdf',

        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword',  # .doc
        'application/vnd.ms-word.document.macroEnabled.12',  # .docm

        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'application/vnd.ms-excel.sheet.macroEnabled.12',  # .xlsm

        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
        'application/vnd.ms-powerpoint',  # .ppt
        'application/vnd.ms-powerpoint.presentation.macroEnabled.12',  # .pptm

        'application/zip',
        'application/x-zip-compressed',
        'application/x-rar-compressed',

        'image/jpeg',
        'image/png',
        'image/gif',

        'text/plain',
    }

    max_size_mb = 10

    def _validate_filename(self, filename: str) -> bool:

        fn = filename.lower()
        dangerous_names = {'autorun.inf', 'desktop.ini', 'thumbs.db', '.ds_store'}
        if fn in dangerous_names:
            return False

        if re.search(r'[<>:"/\\|?*]', fn):
            return False
        parts = fn.split('.')
        if len(parts) > 2:
            for mid in parts[1:-1]:
                if f".{mid}" in self.dangerous_extensions:
                    return False

        return True

    @staticmethod
    def _get_extension(filename: str) -> str:
        return os.path.splitext(filename.lower())[1]

    def _is_valid_extension(self, filename: str) -> bool:
        ext = self._get_extension(filename)
        if ext in self.dangerous_extensions:
            return False
        if ext not in self.allowed_extensions:
            return False
        return True

    def _check_mime(self, file: UploadedFile) -> bool:
        try:
            chunk = file.read(8192)
            file.seek(0)
            mime = magic.from_buffer(chunk, mime=True)
            if mime not in self.allowed_mime_types:
                return False
            return True

        except Exception as e:
            return False

    def _check_size(self, size: int, filename: str) -> bool:
        if size <= 0:
            return False

        if self._get_extension(filename) in ['.jpg', '.jpeg', '.png']:
            size_mb = size / (1024 * 1024)
            if size_mb > self.max_size_mb:
                return False

        return True

    def validate_file_metadata(self, name: str, size: int, mime_type: str) -> dict:
        if not name or not size or not mime_type:
            raise ValidationError("Отсутствуют обязательные метаданные файла")

        if not self._validate_filename(name):
            raise ValidationError("Недопустимое имя файла")

        if not self._is_valid_extension(name):
            raise ValidationError("Недопустимое или опасное расширение файла")

        if mime_type not in self.allowed_mime_types:
            raise ValidationError("MIME-тип файла не соответствует разрешённым")

        if not self._check_size(size, name):
            raise ValidationError(f"Файл пустой или превышает {self.max_size_mb}MB")

        return {
            'name': name,
            'size': size,
            'type': mime_type
        }

    def validate_upload_file(self, file: UploadedFile) -> UploadedFile:
        if not file:
            raise ValidationError("Файл не загружен или отсутствует")

        file_name = file.name
        file_size = getattr(file, 'size', 0)
        file_type = getattr(file, 'content_type', '').split(';')[0]

        self.validate_file_metadata(file_name, file_size, file_type)

        if not self._check_mime(file):
            raise ValidationError("MIME-тип файла не соответствует разрешённым")

        return file


#///////////////////////ЗАКОНСЕРВИРОВАН 04.06.2025
# import os
# import re
# import time
# import subprocess
# import threading
# import psutil
#
# import magic
# import clamd
# import pefile
# import lief
# from oletools.olevba import VBA_Parser
# from PyPDF2 import PdfReader
# from PyPDF2.generic import IndirectObject
#
# from django.core.exceptions import ValidationError
# from django.core.files.uploadedfile import UploadedFile
# from django.conf import settings
#
#
# class FileValidationMixin:
#     """
#     Миксин для валидации и проверки загружаемых файлов на безопасность (локально).
#     Использует:
#       - ClamAV (через pyClamd) для AV-сканирования
#       - oletools + ViperMonkey для анализа Office-макросов
#       - PyPDF2 (+ базовые проверки) для анализа PDF
#       - pefile + LIEF для анализа PE-бинарей
#     """
#
#     # ------------------------------
#     # Конфигурация и параметры
#     # ------------------------------
#
#     # Разрешённые и опасные расширения / MIME-типы
#     allowed_extensions = {
#         '.pdf', '.docx', '.doc', '.docm', '.xlsx', '.xls', '.xlsm', '.pptx', '.ppt', '.pptm',
#         '.jpg', '.jpeg', '.png',
#         '.zip', '.rar',
#         '.txt'
#     }
#     dangerous_extensions = {'.exe', '.dll', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.hta', '.scr', '.pif', '.reg'}
#
#     allowed_mime_types = {
#     # PDF
#     'application/pdf',
#
#     # Word
#     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
#     'application/msword',  # .doc
#     'application/vnd.ms-word.document.macroEnabled.12',  # .docm
#
#     # Excel
#     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
#     'application/vnd.ms-excel',  # .xls
#     'application/vnd.ms-excel.sheet.macroEnabled.12',  # .xlsm
#     'application/vnd.openxmlformats-officedocument.spreadsheetml.template',  # .xltx
#     'application/vnd.ms-excel.template.macroEnabled.12',  # .xltm
#     'application/vnd.ms-excel.sheet.binary.macroEnabled.12',  # .xlsb
#
#     # PowerPoint
#     'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
#     'application/vnd.ms-powerpoint',  # .ppt
#     'application/vnd.ms-powerpoint.presentation.macroEnabled.12',  # .pptm
#     'application/vnd.openxmlformats-officedocument.presentationml.template',  # .potx
#     'application/vnd.ms-powerpoint.template.macroEnabled.12',  # .potm
#     'application/vnd.openxmlformats-officedocument.presentationml.slideshow',  # .ppsx
#     'application/vnd.ms-powerpoint.slideshow.macroEnabled.12',  # .ppsm
#
#     # Архивы
#     'application/zip',
#     'application/x-zip-compressed',
#     'multipart/x-zip',
#     'application/x-rar-compressed',
#     'application/octet-stream',  # (временно можно оставить, если контролируется по расширению)
#
#     # Изображения
#     'image/jpeg',
#     'image/jpg',  # хотя технически идентичен image/jpeg, иногда встречается отдельно
#     'image/png',
#
#     # Текст
#     'text/plain',
#     'text/markdown',  # если предполагается .txt с markdown
#     'application/txt',  # реже, но может встречаться
#
#     # Опционально (если используется LibreOffice или альтернативные офисные редакторы)
#     'application/vnd.oasis.opendocument.text',  # .odt
#     'application/vnd.oasis.opendocument.spreadsheet',  # .ods
#     'application/vnd.oasis.opendocument.presentation',  # .odp
#
#     #Для старых форматов
#     'application/x-ole-storage',
# }
#
#     # Лимиты по размеру
#     max_size_mb = 50
#     max_operation_time = 30  # секунд на любую операцию
#
#     # Настройки ClamAV (хост/порт)
#     clamav_host: str = getattr(settings, 'CLAMAV_HOST', 'localhost')
#     clamav_port: int = getattr(settings, 'CLAMAV_PORT', 3310)
#     clamav_timeout: int = 30
#
#     # Путь к исполняемому файлу ViperMonkey. Если None, эмуляция макросов не делается.
#     vipermonkey_path: str = getattr(settings, 'VIPERMONKEY_PATH', 'vipermonkey')
#
#     def __init__(self):
#         # Для отслеживания таймаута операций
#         self._operation_start_time = 0
#         self._current_operation = None
#         self._operation_lock = threading.Lock()
#
#         # Для отслеживания ресурсов
#         self._start_cpu_time = 0
#         self._start_memory = 0
#         self._resource_stats = {}
#
#     # ------------------------------
#     # Вспомогательные методы
#     # ------------------------------
#
#     def _start_operation(self, name: str):
#         with self._operation_lock:
#             self._operation_start_time = time.time()
#             self._current_operation = name
#
#             # Начало отслеживания ресурсов
#             self._start_cpu_time = time.process_time()
#             self._start_memory = psutil.Process().memory_info().rss
#
#     def _end_operation(self):
#         with self._operation_lock:
#             # Расчет использованных ресурсов
#             cpu_time = time.process_time() - self._start_cpu_time
#             memory_used = psutil.Process().memory_info().rss - self._start_memory
#
#             # Сохранение статистики
#             if self._current_operation:
#                 self._resource_stats[self._current_operation] = {
#                     'cpu_time': cpu_time,
#                     'memory_used': memory_used,
#                     'duration': time.time() - self._operation_start_time
#                 }
#
#     def get_resource_stats(self):
#         """Возвращает статистику использования ресурсов по операциям"""
#         return self._resource_stats
#
#     def _check_timeout(self):
#         with self._operation_lock:
#             elapsed = time.time() - self._operation_start_time
#             if elapsed > self.max_operation_time:
#                 error_msg = f"Превышено время выполнения операции: {self._current_operation} ({elapsed:.1f}s)"
#                 raise ValidationError(error_msg)
#
#     def _validate_filename(self, filename: str) -> bool:
#         """
#         1) Нет опасных имён (autorun.inf, .DS_Store и т.п.)
#         2) Запрещённые символы
#         3) Двойные расширения с опасным расширением в середине (name.exe.jpg)
#         """
#         fn = filename.lower()
#         dangerous_names = {'autorun.inf', 'desktop.ini', 'thumbs.db', '.ds_store'}
#         if fn in dangerous_names:
#             return False
#
#         # Запрет символов <>:"/\|?*
#         if re.search(r'[<>:"/\\|?*]', fn):
#             return False
#
#         # Двойное расширение
#         parts = fn.split('.')
#         if len(parts) > 2:
#             for mid in parts[1:-1]:
#                 if f".{mid}" in self.dangerous_extensions:
#                     return False
#
#         return True
#
#     def _get_extension(self, filename: str) -> str:
#         return os.path.splitext(filename.lower())[1]
#
#     def _is_valid_extension(self, filename: str) -> bool:
#         ext = self._get_extension(filename)
#         if ext in self.dangerous_extensions:
#             return False
#         return ext in self.allowed_extensions
#
#     def _check_mime(self, file: UploadedFile) -> bool:
#         """
#         Проверка MIME-типа через python-magic
#         """
#         try:
#             self._start_operation("mime_check")
#             chunk = file.read(min(8192, getattr(file, 'size', 0)))
#             mime = magic.from_buffer(chunk, mime=True)
#             file.seek(0)
#             if mime not in self.allowed_mime_types:
#                 return False
#             return True
#         except Exception as e:
#             raise ValidationError(f"Ошибка при определении MIME: {e}")
#
#     def _check_size(self, size: int) -> bool:
#         """
#         Проверяет, что файл не пустой и не превышает max_size_mb
#         """
#         if size <= 0:
#             return False
#         size_mb = size / (1024 * 1024)
#         return size_mb <= self.max_size_mb
#
#     # ------------------------------
#     # Основные проверки
#     # ------------------------------
#
#     def scan_clamav(self, file: UploadedFile) -> bool:
#         """
#         Сканирование файла ClamAV (локально)
#         """
#         try:
#             cd = clamd.ClamdNetworkSocket(
#                 host=self.clamav_host,
#                 port=self.clamav_port,
#                 timeout=self.clamav_timeout
#             )
#             file.seek(0)
#             result = cd.instream(file)
#             file.seek(0)
#             if result:
#                 # result — словарь { '/path/to/stream': ('FOUND','Trojan.XYZ') }
#                 for _, (status, signature) in result.items():
#                     if status == 'FOUND':
#                         error_msg = f"Обнаружен вирус: {signature}"
#                         raise ValidationError(error_msg)
#             return True
#         except clamd.ConnectionError:
#             error_msg = "Не удалось подключиться к ClamAV"
#             raise ValidationError(error_msg)
#         except ValidationError:
#             raise
#         except Exception as e:
#             error_msg = f"Ошибка при сканировании ClamAV: {e}"
#             raise ValidationError(error_msg)
#
#     def check_office_macros(self, file: UploadedFile) -> bool:
#         """
#         Для Office-файлов (.docm, .xlsm, .pptm, .doc, .xls, .ppt) проверяет макросы через oletools.
#         Возвращает True, если макросов нет. Иначе — ValidationError.
#         """
#         ext = self._get_extension(file.name)
#         if ext not in {'.docm', '.xlsm', '.pptm', '.doc', '.xls', '.ppt'}:
#             return True
#
#         try:
#             file.seek(0)
#             vbaparser = VBA_Parser(file.name, data=file.read())
#             file.seek(0)
#             if vbaparser.detect_vba_macros():
#                 if self.vipermonkey_path:
#                     try:
#                         temp_path = f"/tmp/{os.path.basename(file.name)}"
#                         with open(temp_path, 'wb') as tmpf:
#                             tmpf.write(file.read())
#                         file.seek(0)
#
#                         proc = subprocess.run(
#                             [self.vipermonkey_path, temp_path],
#                             stdout=subprocess.PIPE,
#                             stderr=subprocess.PIPE,
#                             timeout=self.max_operation_time
#                         )
#                         stdout = proc.stdout.decode(errors='ignore')
#                         stderr = proc.stderr.decode(errors='ignore')
#                         os.remove(temp_path)
#                     except subprocess.TimeoutExpired:
#                         error_msg = "Эмуляция макросов (ViperMonkey) превысила время"
#                         raise ValidationError(error_msg)
#                     except Exception:
#                         error_msg = "Обнаружены VBA-макросы в Office-файле"
#                         raise ValidationError(error_msg)
#                 error_msg = "Обнаружены VBA-макросы в Office-файле"
#                 raise ValidationError(error_msg)
#             return True
#         except ValidationError:
#             raise
#         except Exception as e:
#             error_msg = f"Ошибка при анализе Office-макросов: {e}"
#             raise ValidationError(error_msg)
#
#     def check_pdf(self, file: UploadedFile) -> bool:
#         """
#         Базовый статический анализ PDF с помощью PyPDF2:
#           - запрет зашифрованных
#           - проверка количества страниц
#           - отсутствие OpenAction / Additional Actions
#           - отсутствие AcroForm / XFA
#           - отсутствие JavaScript, EmbeddedFiles, URI, Launch-действий
#         """
#         ext = self._get_extension(file.name)
#         if ext != '.pdf':
#             return True
#
#         try:
#             file.seek(0)
#             reader = PdfReader(file)
#
#             if reader.is_encrypted:
#                 error_msg = "Зашифрованные PDF не поддерживаются"
#                 raise ValidationError(error_msg)
#
#             num_pages = len(reader.pages)
#             if num_pages > getattr(self, 'max_pdf_pages', 1000):
#                 error_msg = f"Превышено число страниц в PDF: {num_pages}"
#                 raise ValidationError(error_msg)
#
#             trailer = reader.trailer.get("/Root")
#             if isinstance(trailer, IndirectObject):
#                 trailer = trailer.get_object()
#
#             # Проверки корня
#             if trailer:
#                 if "/OpenAction" in trailer or "/AA" in trailer:
#                     error_msg = "PDF содержит запрещённые действия (OpenAction/Additional Actions)"
#                     raise ValidationError(error_msg)
#                 if "/AcroForm" in trailer:
#                     error_msg = "PDF содержит интерактивную форму (AcroForm/XFA)"
#                     raise ValidationError(error_msg)
#                 if "/Names" in trailer:
#                     names = trailer.get("/Names")
#                     if isinstance(names, IndirectObject):
#                         names = names.get_object()
#                     for key in ("/JavaScript", "/EmbeddedFiles", "/URI", "/Actions"):
#                         if names and key in names:
#                             error_msg = f"PDF содержит запрещённый элемент в /Names: {key}"
#                             raise ValidationError(error_msg)
#
#             # Проверка аннотаций и действий на страницах
#             for page_ref in reader.pages:
#                 self._check_timeout()
#                 page = page_ref
#                 if isinstance(page, IndirectObject):
#                     page = page.get_object()
#
#                 # Аннотации
#                 annots = page.get("/Annots")
#                 if annots:
#                     if isinstance(annots, IndirectObject):
#                         annots = annots.get_object()
#                     if not isinstance(annots, list):
#                         annots = [annots]
#                     for annot_ref in annots:
#                         if isinstance(annot_ref, IndirectObject):
#                             annot = annot_ref.get_object()
#                         else:
#                             annot = annot_ref
#                         subtype = annot.get("/Subtype")
#                         if subtype in ("/FileAttachment", "/RichMedia", "/Movie", "/Sound", "/3D"):
#                             error_msg = f"PDF содержит опасную аннотацию: {subtype}"
#                             raise ValidationError(error_msg)
#                         if "/AA" in annot or annot.get("/Action") == "/Launch":
#                             error_msg = "PDF содержит аннотацию с опасным действием (AA/Launch)"
#                             raise ValidationError(error_msg)
#
#                 # Дополнительные действия на странице
#                 if "/AA" in page:
#                     error_msg = "PDF содержит Additional Actions на странице"
#                     raise ValidationError(error_msg)
#                 if "/RichMedia" in page or "/3D" in page or "/Sound" in page or "/Movie" in page:
#                     error_msg = "PDF содержит мультимедиа-объекты (RichMedia/3D/Sound/Movie)"
#                     raise ValidationError(error_msg)
#                 if "/Action" in page and page.get("/Action") == "/Launch":
#                     error_msg = "PDF содержит Launch-действие на странице"
#                     raise ValidationError(error_msg)
#
#             return True
#         except ValidationError:
#             raise
#         except Exception as e:
#             error_msg = f"Ошибка при проверке PDF: {e}"
#             raise ValidationError(error_msg)
#         finally:
#             file.seek(0)
#
#     def check_pe(self, file: UploadedFile) -> bool:
#         """
#         Статический анализ PE-бинарей (.exe, .dll):
#           - проверка структуры секций (непустые, корректные имена)
#           - наличие или отсутствие цифровой подписи
#         """
#         ext = self._get_extension(file.name)
#         if ext not in {'.exe', '.dll'}:
#             return True
#
#         try:
#             temp_path = f"/tmp/{os.path.basename(file.name)}"
#             with open(temp_path, 'wb') as tmpf:
#                 tmpf.write(file.read())
#             file.seek(0)
#
#             # Анализ через pefile
#             pe = pefile.PE(temp_path, fast_load=True)
#             pe.parse_data_directories(directories=[
#                 pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_SECURITY"]
#             ])
#
#             # Проверяем, что есть хотя бы одна секция .text
#             section_names = [sec.Name.decode(errors='ignore').rstrip('\x00') for sec in pe.sections]
#             if not any(name.lower().startswith('text') for name in section_names):
#                 error_msg = "PE-файл не содержит секцию .text или она повреждена"
#                 raise ValidationError(error_msg)
#
#             # Проверяем цифровую подпись (через LIEF)
#             bie = lief.parse(temp_path)
#             has_signature = bie.has_signature
#             if not has_signature:
#                 print(f"[WARNING] PE-файл не имеет цифровой подписи: {file.name}")
#
#             os.remove(temp_path)
#             return True
#         except ValidationError:
#             raise
#         except Exception as e:
#             error_msg = f"Ошибка при анализе PE-файла: {e}"
#             raise ValidationError(error_msg)
#         finally:
#             try:
#                 if os.path.exists(temp_path):
#                     os.remove(temp_path)
#             except Exception:
#                 pass
#
#     # ------------------------------
#     # Главный метод валидации
#     # ------------------------------
#
#     def validate_upload_file(self, file: UploadedFile) -> UploadedFile:
#         """
#         Основной метод-оркестратор. Поэтапно:
#           1. Проверка имени
#           2. Проверка расширения
#           3. Проверка MIME (magic)
#           4. Проверка размера
#           5. Скан ClamAV
#           6. Специфичные проверки по расширению:
#              - Office-макросы (oletools + ViperMonkey)
#              - PDF (статический анализ)
#              - PE-бинарь (pefile + LIEF)
#           7. Если всё ок — возвращает файл, иначе бросает ValidationError.
#         """
#         try:
#             # 1) Проверка наличия
#             if not file:
#                 error_msg = "Файл не загружен или отсутствует"
#                 raise ValidationError(error_msg)
#
#             file_name = file.name
#             file_size = getattr(file, 'size', 0)
#
#             # 1) Имя
#             if not self._validate_filename(file_name):
#                 error_msg = "Недопустимое имя файла"
#                 raise ValidationError(error_msg)
#
#             # 2) Расширение
#             if not self._is_valid_extension(file_name):
#                 error_msg = f"Недопустимое или опасное расширение: {file_name}"
#                 raise ValidationError(error_msg)
#
#             # 3) MIME
#             if not self._check_mime(file):
#                 error_msg = "MIME-тип файла не соответствует разрешённым"
#                 raise ValidationError(error_msg)
#
#             # 4) Размер
#             if not self._check_size(file_size, file_name):
#                 error_msg = f"Файл пустой или превышает {self.max_size_mb} MB"
#                 raise ValidationError(error_msg)
#
#             # 5) ClamAV
#             self.scan_clamav(file)
#
#             # 6) Специальные проверки
#             ext = self._get_extension(file_name)
#             if ext in {'.docm', '.xlsm', '.pptm', '.doc', '.xls', '.ppt'}:
#                 self.check_office_macros(file)
#
#             if ext == '.pdf':
#                 self.check_pdf(file)
#
#             if ext in {'.exe', '.dll'}:
#                 self.check_pe(file)
#
#             return file
#
#         except ValidationError:
#             raise
#         except Exception as e:
#             error_msg = f"Ошибка при валидации файла: {e}"
#             raise ValidationError(error_msg)
#         finally:
#             # Вывод итоговой статистики
#             print("\n[INFO] Итоговая статистика использования ресурсов:")
#             for op, stats in self._resource_stats.items():
#                 print(f"[INFO] {op}:")
#                 print(f"  - CPU время: {stats['cpu_time']:.2f}с")
#                 print(f"  - Использовано памяти: {stats['memory_used']/1024/1024:.2f}MB")
#                 print(f"  - Длительность: {stats['duration']:.2f}с")
