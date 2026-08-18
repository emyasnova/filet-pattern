# Filet Pattern

Репозиторий содержит FastAPI backend и frontend редактора схем филейного
вязания. PostgreSQL для локальной разработки запускается через Docker Compose.

## Требования

- Docker с поддержкой команды `docker compose`;
- Python 3.11 или новее для локального запуска backend.

## Запуск PostgreSQL

Настройки по умолчанию уже заданы в `compose.yaml`. Чтобы изменить их, создайте
локальный `.env` из шаблона:

```bash
cp .env.example .env
```

Запустите PostgreSQL из корня репозитория:

```bash
docker compose up -d
```

Проверьте состояние контейнера:

```bash
docker compose ps
```

После запуска база доступна со следующими параметрами:

```text
host: localhost
port: 5432
database: filet_pattern
user: filet
password: filet
connection URL: postgresql://filet:filet@localhost:5432/filet_pattern
```

Если значения переопределены в `.env`, используйте их и в строке подключения.

Если локальный порт `5432` уже занят, задайте другой порт в `.env`, например:

```dotenv
POSTGRES_PORT=55432
```

Тогда PostgreSQL будет доступен на `localhost:55432`.

Просмотр логов PostgreSQL:

```bash
docker compose logs -f postgres
```

Открыть интерактивный `psql` внутри контейнера:

```bash
docker compose exec postgres psql -U filet -d filet_pattern
```

Остановить контейнер, сохранив данные:

```bash
docker compose down
```

Данные хранятся в именованном volume `postgres_data`. Команда ниже удаляет
контейнер вместе со всеми локальными данными PostgreSQL:

```bash
docker compose down -v
```

## Локальный запуск backend

На текущем этапе Compose запускает только PostgreSQL. Backend запускается
локально:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
python3 -m alembic upgrade head
python3 -m uvicorn app.main:app --reload
```

Backend будет доступен по адресу `http://127.0.0.1:8000`, Swagger UI — по
адресу `http://127.0.0.1:8000/docs`.

Подробности API и тестирования находятся в [`backend/README.md`](backend/README.md).

Backend читает каталог паттернов из PostgreSQL. После изменения схемы всегда
применяйте миграции командой `python3 -m alembic upgrade head` из каталога
`backend`.

## Локальный запуск frontend

После запуска PostgreSQL, миграций и backend откройте второй терминал:

```bash
cd frontend
npm install
npm run dev
```

Vite проксирует запросы `/api` на backend по адресу `http://127.0.0.1:8000`.

В панели «Мотивы» кнопка `+` открывает импорт паттерна из PNG/JPEG. Интерфейс
автоматически определяет размер сетки, позволяет скорректировать пороги и
клетки, затем сохранить имя, категорию и теги в PostgreSQL.
