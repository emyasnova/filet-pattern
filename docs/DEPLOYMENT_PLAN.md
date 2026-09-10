# Публичный запуск Filet Pattern

## Выбор платформы

Для ваших условий — публичный MVP, бюджет $5–10, без администрирования сервера — использовать:

- **Railway Hobby** для единого контейнера React + FastAPI;
- **Neon Free** для PostgreSQL;
- собственный основной домен, `www` перенаправлять на него;
- регион Railway `EU West / Amsterdam`, Neon `AWS Europe / Frankfurt`.

Railway Hobby стоит минимум $5 в месяц и включает первые $5 потреблённых ресурсов; превышение оплачивается отдельно. Нужна поддерживаемая банковская карта. Neon Free предоставляет 0,5 GB и 100 CU-hours в месяц. [Railway pricing](https://docs.railway.com/pricing/plans), [Neon pricing](https://neon.com/pricing)

Альтернативы:

- Render + Neon позволяет начать бесплатно, но backend засыпает и первый запрос будет медленным.
- Один Render с managed PostgreSQL проще организационно, но бесплатная БД удаляется через 30 дней.
- VPS дешевле при постоянной нагрузке, но требует самостоятельных обновлений, TLS, firewall и backup.
- Раздельные frontend/backend дают лучший CDN, но добавляют CORS, отдельные домены и несколько deploy-процессов.

## Подготовка приложения

- Добавить корневой multi-stage `Dockerfile`: Node собирает Vite, Python устанавливает backend, итоговый образ содержит только FastAPI и `frontend/dist`.
- FastAPI раздаёт собранный frontend после регистрации `/api`, `/health`, `/docs`; неизвестные frontend-маршруты возвращают `index.html`.
- Контейнер запускает `alembic upgrade head`, затем Uvicorn на переменной Railway `PORT`.
- Добавить `railway.toml`: Dockerfile build, один экземпляр, restart on failure, healthcheck `/ready`, регион Amsterdam.
- Backend принимает стандартный `DATABASE_URL` Neon, принудительно использует драйвер `postgresql+psycopg` и SSL; локальные `POSTGRES_*` сохраняются как fallback.
- Добавить `/ready`, выполняющий `SELECT 1`; существующий `/health` оставить простым liveness endpoint.
- Изображения продолжать обрабатывать только в памяти; persistent volume не требуется.

## Защита публичного приложения

- Публично оставить редактор, экспорт и GET-каталог паттернов.
- В первом публичном релизе отключить production-доступ к
  `POST /api/v1/images/size`, `/api/v1/patterns/preview` и
  `POST /api/v1/patterns` через серверный feature flag
  `PATTERN_CREATION_ENABLED=false`.
- Скрывать кнопку `+` и весь интерфейс импорта, когда создание отключено.
- Добавить публичный `GET /api/v1/config`, чтобы frontend получал значение
  `patternCreationEnabled` от backend, а не из отдельного build-time секрета.
- Не добавлять временные `ADMIN_PASSWORD`, admin-cookie и endpoints входа:
  этот код вскоре был бы заменён телефонной авторизацией.
- Для локальной разработки и тестирования разрешать явно включить
  `PATTERN_CREATION_ENABLED=true`; production-значение по умолчанию остаётся
  `false`.
- Ограничить частоту публичных запросов чтения и сохранить лимит загрузки
  изображения 10 MiB для будущего защищённого импорта.
- Добавить trusted-host, canonical redirect с `www` на основной домен и базовые security headers.

### Следующий этап: авторизация по телефону

- Добавить пользователей, нормализованные уникальные номера телефонов и роли
  `user`/`admin` в PostgreSQL через Alembic migration.
- Интегрировать SMS-провайдера через отдельный интерфейс, не связывая доменную
  логику с конкретным поставщиком.
- Реализовать выдачу и проверку одноразовых кодов с коротким TTL, лимитами
  отправки и ввода, защитой от перебора и SMS-фрода.
- Использовать серверные отзываемые сессии в HttpOnly/Secure/SameSite cookie;
  не хранить токены авторизации в localStorage.
- Назначить вашему пользователю роль `admin` отдельной безопасной bootstrap-командой.
- После внедрения авторизации разрешить endpoints импорта только роли `admin`,
  а публичным пользователям оставить чтение каталога и редактор.

## Развёртывание и данные

1. Создать Neon-проект во Frankfurt и получить direct connection string.
2. Создать Railway Hobby project из GitHub-репозитория, выбрать Amsterdam и передать `DATABASE_URL`, `PUBLIC_ORIGIN`, `CANONICAL_HOST` и `PATTERN_CREATION_ENABLED=false`.
3. Получить временный Railway-домен, проверить `/ready`, frontend, миграции и недоступность production-import endpoints.
4. Подключить основной домен и `www` в Railway, установить выданные Railway DNS-записи и дождаться HTTPS.
5. Включить GitHub autodeploy только для основной ветки; deployment считается успешным после `/ready`.
6. Добавить ежедневный GitHub Actions backup:
   - `pg_dump` → gzip → AES-256 encryption;
   - `DATABASE_URL` и пароль шифрования хранятся в GitHub Secrets;
   - хранить зашифрованные artifacts 30 дней;
   - поддержать ручной `workflow_dispatch`;
   - документировать расшифровку и восстановление в новую Neon DB.

Railway использует `PORT` для healthcheck и переключает deployment после ответа `200`. [Railway healthchecks](https://docs.railway.com/deployments/healthchecks)

## Проверка

- Unit/API-тесты: DATABASE_URL fallback, feature flag, закрытые production POST и публичные GET.
- Integration: чистая PostgreSQL → миграции → seed → чтение каталога; создание паттерна проверяется только при явном локальном включении feature flag.
- Docker smoke test: сборка образа, `/`, `/assets`, `/api`, `/docs`, `/health`, `/ready`, SPA fallback.
- Production smoke test: загрузка frontend, чтение каталога и отказ всех endpoints импорта; локальный smoke test отдельно проверяет распознавание и сохранение при включённом feature flag.
- Backup test: ручной workflow, скачивание, расшифровка и восстановление в отдельную тестовую БД.
- DNS test: HTTPS на основном домене, redirect `www`, отсутствие mixed content и CORS-запросов.

## Допущения

- Приложение работает в одном Railway instance; горизонтальное масштабирование пока не требуется.
- В первом публичном релизе создавать паттерны через production UI нельзя;
  исходный каталог создаётся seed-миграцией, а новые production-записи не
  добавляются до появления телефонной авторизации.
- После телефонной авторизации создавать паттерны сможет только пользователь с ролью `admin`.
- Репозиторий доступен Railway через GitHub.
- Конкретное имя домена будет подставлено в `PUBLIC_ORIGIN` при настройке.
- Если оплата Railway недоступна, тот же Docker-образ переносится на Render; Neon и остальные настройки сохраняются.
