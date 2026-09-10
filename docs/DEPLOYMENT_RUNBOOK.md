# Filet Pattern deployment runbook

## 1. Локальная production-проверка

Требуются Docker Compose и `curl`. Из корня репозитория:

```bash
docker compose -f compose.production-local.yaml build
docker compose -f compose.production-local.yaml up -d
docker compose -f compose.production-local.yaml ps
./scripts/smoke-production.sh
```

Startup script перед каждым запуском выполняет `alembic upgrade head`; миграция
идемпотентно создаёт схему и seed-каталог на чистой БД. Перезапуск без потери
данных проверяется так:

```bash
docker compose -f compose.production-local.yaml restart app postgres
./scripts/smoke-production.sh
```

Для ручной проверки разрешённого импорта пересоздайте только приложение с явным
локальным flag, затем загрузите PNG/JPEG через кнопку `+` и сохраните паттерн:

```bash
PATTERN_CREATION_ENABLED=true docker compose -f compose.production-local.yaml up -d --force-recreate app
```

Верните безопасный режим и повторите smoke test:

```bash
PATTERN_CREATION_ENABLED=false docker compose -f compose.production-local.yaml up -d --force-recreate app
./scripts/smoke-production.sh
```

Полный набор проверок репозитория:

```bash
cd backend && .venv/bin/python -m pytest
cd ../frontend && npm test && npm run lint && npm run build
cd .. && docker build -t filet-pattern:local .
```

Остановка сохраняет PostgreSQL volume:

```bash
docker compose -f compose.production-local.yaml down
```

Удалять volume для повторной проверки чистой БД следует только осознанно:
`docker compose -f compose.production-local.yaml down -v`.

### Локальный backup round trip

Нужны `pg_dump`, `psql`, `createdb`, `gzip` и OpenSSL. Значения вводятся в
локальной оболочке и не записываются в репозиторий:

```bash
export DATABASE_URL='postgresql://filet:local-production-only@localhost:55433/filet_pattern'
export BACKUP_PASSWORD='local-test-password'
export PGPASSWORD='local-production-only'
./scripts/backup-postgres.sh backup.sql.gz.enc
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -pass env:BACKUP_PASSWORD -in backup.sql.gz.enc | gzip -dc > restore.sql
createdb -h localhost -p 55433 -U filet filet_pattern_restore
psql 'postgresql://filet:local-production-only@localhost:55433/filet_pattern_restore' -f restore.sql
psql 'postgresql://filet:local-production-only@localhost:55433/filet_pattern_restore' \
  -c '\dt' -c 'select count(*) from patterns;'
```

Используйте отдельную БД назначения: восстановление поверх production запрещено.

## 2. Действия после создания облачных аккаунтов

### Neon

1. Создайте PostgreSQL project в европейском регионе и отдельную production DB.
2. Скопируйте connection string с TLS; не сохраняйте её в файлах репозитория.
3. Проверьте доступ с локального `psql`, затем используйте строку как
   `DATABASE_URL` в Railway и GitHub Secrets.

### Railway

1. Создайте project из GitHub-репозитория. Railway прочитает `railway.toml` и
   соберёт корневой `Dockerfile`.
2. Задайте runtime variables из таблицы ниже. Оставьте один instance; healthcheck
   `/ready` должен стать зелёным до подключения трафика.
3. После deploy проверьте `/health`, `/ready`, `/`, каталог и запрет всех трёх
   POST endpoints. Не включайте создание паттернов до телефонной авторизации.
4. Регулярно проверяйте Railway Usage и установите budget alerts. На дату
   подготовки runbook Railway Hobby имеет минимальное потребление **$5/месяц**,
   включаемое в usage. Neon Free может дать **$0/месяц** при малой нагрузке;
   ориентир Neon Launch для intermittent load и 1 GB — **около $15/месяц**.
   Поэтому ожидаемый MVP-бюджет — от **$5/месяц** на бесплатном Neon либо около
   **$20/месяц** с Neon Launch, плюс домен и превышение compute/storage/egress.
   Перед оплатой обязательно перепроверьте актуальные страницы
   [Railway Pricing](https://railway.com/pricing) и
   [Neon Pricing](https://neon.com/pricing): usage может изменить итоговую сумму.

| Переменная | Где | Обязательна | Значение |
|---|---|---:|---|
| `DATABASE_URL` | Railway, GitHub Secret | да | Neon PostgreSQL URL |
| `PUBLIC_ORIGIN` | Railway | да | `https://` + основной домен |
| `CANONICAL_HOST` | Railway | да | hostname без схемы |
| `PATTERN_CREATION_ENABLED` | Railway | да | `false` |
| `FRONTEND_DIST_DIR` | image default | нет | `/app/frontend/dist` |
| `PORT` | Railway-managed | да | выдаёт Railway |
| `BACKUP_PASSWORD` | GitHub Secret | да | отдельная сильная фраза |

`POSTGRES_*` предназначены только для локального fallback. Секреты не передаются
как Docker build args.

### GitHub backup

Добавьте repository secrets `DATABASE_URL` и `BACKUP_PASSWORD`, затем вручную
запустите workflow **PostgreSQL backup**. Он хранит только AES-256-CBC encrypted
artifact 30 дней. Скачайте artifact и выполните команды расшифровки/восстановления
из раздела round trip, обязательно в отдельную БД. Для Neon после проверки
создайте новую branch/database, восстановите туда dump, сравните таблицы и число
паттернов и только затем переключайте приложение на проверенный URL.

### Домен и DNS

Добавьте custom domain в Railway, скопируйте выданные Railway DNS targets в
регистратор, дождитесь TLS, затем задайте `PUBLIC_ORIGIN` и `CANONICAL_HOST`.
Настройте `www` на тот же сервис: приложение перенаправит его на canonical host.

### Rollback

В Railway откройте историю deployments, выберите предыдущий успешный deployment
и выполните **Rollback/Redeploy**. Не откатывайте миграции автоматически: сначала
проверьте совместимость предыдущего приложения с текущей схемой. После rollback
проверьте `/ready`, каталог и frontend. Если проблема в данных, восстановите
зашифрованный backup в отдельную Neon database и переключите `DATABASE_URL`
только после проверки.

MVP не включает несколько Uvicorn workers или горизонтальное масштабирование.
