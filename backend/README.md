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
* изображения

## API

* `GET /health`
* `POST /api/v1/schemes/generate`

## Run

Before local run, activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -e .[dev]
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
