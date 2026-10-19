# Сервис управления рассылками (Django)

Веб-приложение для управления рассылками сообщений клиентам. Позволяет создавать базы получателей, шаблоны писем, планировать и автоматически отправлять рассылки, а также отслеживать статистику доставки.

## 📋 Функциональные возможности

- **Управление клиентами:** создание, просмотр, редактирование и удаление получателей (Email, ФИО, комментарий).
- **Управление сообщениями:** создание шаблонов писем (тема, тело).
- **Управление рассылками:** настройка временного окна (начало/конец), выбор сообщения и списка получателей.
- **Валидация:** проверка корректности дат (начало не в прошлом, конец позже начала).
- **Динамический статус:** рассылка автоматически меняет статус (`Создана`, `Запущена`, `Завершена`) в зависимости от текущего времени.
- **Отправка сообщений:**
  - Вручную (по кнопке «Отправить сейчас»).
  - Автоматически (через Celery Beat — проверка каждую минуту).
- **История попыток:** фиксация каждой отправки (дата, статус `Успешно`/`Не успешно`, ответ сервера).
- **Аутентификация:** регистрация с подтверждением email, вход/выход, восстановление пароля.
- **Роли доступа:**
  - *Пользователь:* управляет только своими данными.
  - *Менеджер:* просматривает всё, может блокировать пользователей и отключать рассылки.
- **Статистика:** главная страница с дашбордом (общее число рассылок, активные, получатели, успешные/неуспешные попытки).
- **Кэширование:** серверное (Redis) для страниц и QuerySet, клиентское (HTTP-заголовки).

## 🛠 Технологический стек

- **Python 3.14**
- **Django 5.2 LTS**
- **Celery 5.6** + **django-celery-beat 2.9**
- **Redis 7** (Docker) — кэш и брокер сообщений
- **SQLite** — база данных (для разработки)
- **Poetry** — управление зависимостями
- **Bootstrap 5** — UI (через CDN)
- **Gitflow** — методология ветвления

## 📁 Структура проекта

```
coursework_4/
├── config/                 # Настройки Django
│   ├── settings.py
│   ├── celery.py           # Конфигурация Celery
│   └── urls.py
├── mailing/                # Приложение рассылок
│   ├── management/        # Кастомные команды (seed_data)
│   ├── migrations/
│   ├── mixins.py           # Миксины для прав доступа
│   ├── models.py           # Recipient, Message, Mailing, Attempt
│   ├── services.py         # Логика отправки
│   ├── tasks.py            # Celery-задачи
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── users/                  # Приложение аутентификации
│   ├── management/
│   ├── apps.py             # Свойство is_manager
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── templates/              # HTML-шаблоны (Bootstrap)
│   ├── base.html
│   ├── mailing/
│   ├── users/
│   └── registration/
├── static/                 # Статические файлы
├── .env.example            # Пример переменных окружения
├── docker-compose.yml      # Redis
├── pyproject.toml          # Poetry
└── README.md
```

## 🚀 Установка и запуск

### Предварительные требования

- Python 3.14
- Poetry
- Docker и Docker Compose

### 1. Клонирование и установка зависимостей

```bash
git clone <url-репозитория>
cd coursework_4
poetry install
```

### 2. Настройка переменных окружения

Скопируй `.env.example` в `.env` и заполни:

```bash
cp .env.example .env
```

Пример `.env`:

```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True

# Email (console backend для разработки)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@mailing.local

# Redis
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
```

### 3. Запуск Redis

```bash
docker compose up -d
```

Проверка:
```bash
docker exec -it mailing-redis redis-cli ping
# → PONG
```

### 4. Миграции и заполнение тестовыми данными

```bash
poetry run python manage.py migrate
poetry run python manage.py fill_db --clear
poetry run python manage.py create_manager
```

Команда `fill_db` создаст:
- 8 получателей
- 5 сообщений
- 5 рассылок во всех статусах (активная, будущая, завершённая, отключённая)
- историю попыток
- суперпользователя `admin` (пароль `admin123`, если не было)
Команда `create_manager` создаст:
- менеджера `manager` (пароль `manager123`)

### 5. Запуск сервера

```bash
poetry run python manage.py runserver
```

Приложение доступно по адресу: `http://127.0.0.1:8000/`

### 6. Запуск Celery (для автоматической отправки)

Понадобятся **два дополнительных терминала**:

**Терминал 1 — Worker:**
```bash
poetry run celery -A config worker -l info -P solo
```
> Флаг `-P solo` обязателен на Windows.

**Терминал 2 — Beat (планировщик):**
```bash
poetry run celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

> Периодическая задача `Auto send mailings` должна быть создана в админке (`/admin/` → **Periodic Tasks**). Интервал: **1 минута**.

## 🧪 Проверка работоспособности (Сценарии)

### 1. Валидация рассылок
- Создай рассылку с датой в прошлом (> 5 минут назад) → ошибка *«Дата начала не может быть в прошлом»*.
- Создай рассылку с `end_time` раньше `start_time` → ошибка *«Дата окончания должна быть позже даты начала»*.

### 2. Ручная отправка
- Создай рассылку с `start = сейчас − 2 мин`, `end = сейчас + 10 мин`.
- Открой детальную страницу → статус «Запущена» → нажми «Отправить сейчас».
- В терминале `runserver` появятся письма (console backend), на странице — попытки со статусом «Успешно».

### 3. Автоматическая отправка
- Создай рассылку с `start = сейчас + 1 мин`, `end = сейчас + 10 мин`.
- Не нажимай кнопку.
- Подожди 1–2 минуты. В терминале Worker появится строка `Task mailing.tasks.send_scheduled_mailings[...] received`.
- В деталях рассылки появятся попытки.

### 4. Роли и ограничения
- **Обычный пользователь:** видит только свои рассылки. При попытке открыть чужую по прямому URL (`/mailings/1/`) — **404**.
- **Менеджер:** видит все рассылки, может отключать их (кнопка «Отключить»), но не может редактировать чужие. Может блокировать пользователей через `/users/manage/list/`.

### 5. Кэширование
```bash
docker exec -it mailing-redis redis-cli
> keys *
```
Должны быть ключи:
- `:1:views.decorators.cache...` (главная страница)
- `:1:mailing_list_1` (список рассылок пользователя с ID=1)

При создании/редактировании/удалении рассылки кэш сбрасывается автоматически.

## 🌿 Gitflow (Ветвление)

Проект разработан по методологии Gitflow:

- `main` — стабильные релизы.
- `develop` — интеграционная ветка.
- `feature/*` — новые функции (например, `feature/crud-mailings`, `feature/caching`).
- `release/*` — подготовка релиза (например, `release/1.0`).
- `hotfix/*` — срочные исправления.

**Релиз 1.0:**
```bash
git checkout develop
git checkout -b release/1.0
# ...
git checkout main
git merge --no-ff release/1.0 -m "Release v1.0"
git tag -a v1.0 -m "First stable release"
git checkout develop
git merge --no-ff release/1.0 -m "Merge release v1.0 into develop"
git branch -d release/1.0
```

## 📊 Основные модели

| Модель | Описание |
|--------|----------|
| `Recipient` | Получатель (email, ФИО, комментарий, владелец) |
| `Message` | Шаблон письма (тема, тело, владелец) |
| `Mailing` | Рассылка (start_time, end_time, status, message, recipients, is_disabled) |
| `Attempt` | Попытка отправки (attempt_time, status, server_response, mailing) |

## 🔧 Кастомные команды

```bash
# Заполнение БД тестовыми данными
poetry run python manage.py fill_db --clear

# Создание группы manager и пользователя manager
poetry run python manage.py create_manager
```

## 📝 Лицензия

Учебный проект.
```
