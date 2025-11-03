#!/bin/sh
set -ex

echo "Ожидание загрузки проекта..."
until cd /usr/src/app/; do
  echo "Ожидание сервера..."
  sleep 2
done

echo "Применяем миграции..."
python manage.py migrate || echo "Предупреждение: Нет ответа от БД"

echo "Загружаем фикстуры слотов..."
python manage.py load_slot_packages_ready_tasks || echo "Предупреждение: Ошибка загрузки фикстур json файлов"

echo "Загружаем фикстуры банков..."
python manage.py load_bank_id || echo "Предупреждение: Ошибка загрузки фикстур json файлов"

echo "Загружаем правила..."
python manage.py load_rules || echo "Предупреждение: Ошибка загрузки правил"

echo "Загружаем JSON файлы..."
python manage.py load_jsonfiles || echo "Предупреждение: Ошибка JSON файлы"

echo "Собираем статику..."
python manage.py collectstatic --noinput || exit 1

# Создаем лог-файлы
mkdir -p /usr/src/app/logs
touch /usr/src/app/logs/gunicorn.log /usr/src/app/logs/daphne.log
chmod 666 /usr/src/app/logs/gunicorn.log /usr/src/app/logs/daphne.log

# Запускаем Gunicorn в фоновом режиме
echo "Запуск Gunicorn..."
gunicorn studium_backend.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --log-level info \
  --access-logfile /usr/src/app/logs/gunicorn.log \
  --error-logfile /usr/src/app/logs/gunicorn.log &

# Запускаем Daphne для WebSocket
echo "Запуск Daphne..."
daphne -b 0.0.0.0 -p 8001 studium_backend.asgi:application \
  >> /usr/src/app/logs/daphne.log 2>&1 