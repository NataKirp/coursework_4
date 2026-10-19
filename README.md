# Сервис рассылок (Django)

Веб-приложение для управления рассылками сообщений клиентам.

## Стек
- Python 3.14, Django 5.2 LTS
- Celery 5.6, django-celery-beat 2.9
- Redis 7 (Docker) — кэш и брокер
- SQLite (разработка)

## Ветки
Gitflow: `main`, `develop`, `feature/*`, `release/*`.

## Запуск
1. `poetry install`
2. `docker compose up -d`
3. `poetry run python manage.py migrate`
4. `poetry run python manage.py fill_db`
5. `poetry run python manage.py runserver`