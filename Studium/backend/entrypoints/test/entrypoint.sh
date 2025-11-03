#!/bin/sh

set -e

echo "Ожидание загрузки проекта..."
until cd /usr/src/app/; do
  echo "Ожидание сервера..."
  sleep 2
done

echo "Применяем миграции..."
python manage.py migrate || echo "Предупреждение: Нет ответа от БД"

echo "Загружаем фикстуры..."
python manage.py load_jsonfiles || echo "Предупреждение: Ошибка загрузки фикстур"
echo "Загружаем фикстуры предложений слотов..."
python manage.py load_slot_packages_ready_tasks || echo "Предупреждение: Ошибка загрузки фикстур"
echo "Загружаем правила..."
python manage.py load_rules || echo "Предупреждение: Ошибка загрузки правил"
echo "Собираем статику..."
python manage.py collectstatic --noinput || exit 1

echo "Создаем администратора..."
python manage.py create_admin_user || echo "Предупреждение: Ошибка создания администратора"

echo "Запуск тестов authentication..."
python manage.py test authentication  --keepdb || echo "Предупреждение: Ошибка при запуске тестов authentication"

echo "Запуск тестов feedbacks..."
python manage.py test feedbacks --keepdb || echo "Предупреждение: Ошибка при запуске тестов feedbacks"

echo "Запуск тестов jsons..."
python manage.py test jsons --keepdb || echo "Предупреждение: Ошибка при запуске тестов jsons"

echo "Запуск тестов notifications..."
python manage.py test notifications --keepdb || echo "Предупреждение: Ошибка при запуске тестов notifications"

echo "Запуск тестов ready_tasks..."
python manage.py test ready_tasks --keepdb || echo "Предупреждение: Ошибка при запуске тестов ready_tasks"

echo "Запуск тестов reports..."
python manage.py test reports --keepdb || echo "Предупреждение: Ошибка при запуске тестов reports"

echo "Запуск тестов rules..."
python manage.py test rules --keepdb || echo "Предупреждение: Ошибка при запуске тестов rules"

echo "Запуск тестов storage..."
python manage.py test storage --keepdb || echo "Предупреждение: Ошибка при запуске тестов storage"

echo "Запуск тестов users..."
python manage.py test users --keepdb || echo "Предупреждение: Ошибка при запуске тестов users"

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