# Backend - Генератор схем филейного вязания

## Описание

Backend генерирует схемы филейного вязания по тексту.

Он:

* принимает JSON
* валидирует данные
* генерирует схему
* возвращает JSON

## Версия 1

Включено:

* FastAPI
* генерация схем
* валидация

Не включено:

* БД
* авторизация
* сохранение
* генерация изображений

## API

* `GET /health`
* `POST /api/v1/schemes/generate`
* `POST /api/v1/images/size`
* `GET /api/v1/patterns`
* `GET /api/v1/categories`
* `GET /api/v1/tags`

### Каталог паттернов

`GET /api/v1/patterns` возвращает паттерны из PostgreSQL от новых к старым.
Доступны необязательные параметры `search`, `category` и повторяемый `tags`:

```bash
curl 'http://localhost:8000/api/v1/patterns?search=rose&category=ornament&tags=flower&tags=роза'
```

При нескольких `tags` возвращаются только паттерны, содержащие все указанные
теги. Справочники доступны через `/api/v1/categories` и `/api/v1/tags`.

### Создание паттерна из изображения

Сценарий состоит из трёх запросов:

1. `POST /api/v1/images/size` определяет исходный размер сетки.
2. `POST /api/v1/patterns/preview` принимает тот же файл, размеры и пороги,
   возвращая обрезанную матрицу `0/1/null`.
3. `POST /api/v1/patterns` сохраняет отредактированную матрицу, имя, категорию
   и теги.

Preview использует in-memory ядро `tools/glyph_import` и не создаёт временных
JSON, preview или debug-файлов. Пустой фон, связанный с границей матрицы,
становится прозрачным (`null`), а замкнутые белые области остаются `0`.

### Определение размера схемы по изображению

`POST /api/v1/images/size` принимает PNG или JPEG в поле `file` запроса
`multipart/form-data` и возвращает ширину и высоту схемы в клетках. Дробные
оценки округляются до ближайшего целого.

Пример запроса:

```bash
curl -X POST http://localhost:8000/api/v1/images/size \
  -F "file=@chart.png"
```

Успешный ответ:

```json
{
  "width": 120,
  "height": 80
}
```

Если файл пуст, повреждён, имеет неподдерживаемый формат или сетку определить
невозможно, API возвращает `422 Unprocessable Entity`:

```json
{
  "detail": "Could not detect a grid in the uploaded image"
}
```

## Run

Before local run, activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1

source .venv/bin/activate
```

Install dependencies:

```powershell
python -m pip install -e .[dev]
```

Apply database migrations:

```powershell
python -m alembic upgrade head
```

Run the server:

```powershell
python -m uvicorn app.main:app --reload
```

Run tests:

```powershell
python -m pytest
```

## Документы

* `PRODUCT_REQUIREMENTS.md`
* `DOMAIN.md`
* `GENERATION_RULES.md`
* `API_CONTRACT.md`
* `ARCHITECTURE.md`
* `TASKS.md`

## Подход

Разработка ведётся пошагово с использованием Codex.
