# Резервное копирование Neon через GitHub Actions

## 1. Отправить подготовленные файлы в GitHub

Workflow: `.github/workflows/postgres-backup.yml`.
Скрипт: `scripts/backup-postgres.sh` (Bash, `pipefail`).
Workflow должен находиться в основной (default) ветке репозитория.
Клиент закреплён на PostgreSQL 17 — эта версия выбрана для базы проекта.
Если сервер Neon обновлён до более новой major-версии, обновите и клиент.

## 2. Добавить repository secrets

GitHub → репозиторий → **Settings → Secrets and variables → Actions →
Secrets → New repository secret**. Создайте:

| Name | Secret |
|---|---|
| `DATABASE_URL` | Полная direct connection string рабочей БД Neon, включая пароль и параметры SSL. Начало `postgresql://`, без команды `psql` и внешних кавычек. |
| `BACKUP_PASSWORD` | Отдельный длинный случайный пароль для шифрования, созданный и сохранённый в менеджере паролей. |

Это Repository secrets, не Variables и не Environment secrets: workflow не
привязан к GitHub Environment. Настройки Railway сюда автоматически не переходят.
`BACKUP_PASSWORD` не является паролем PostgreSQL. Сохраните его вне GitHub:
после добавления Secret нельзя прочитать обратно. При смене пароля сохраняйте
старый, пока нужны архивы, зашифрованные им.

## 3. Запустить и скачать первую копию

1. Репозиторий → **Actions → PostgreSQL backup → Run workflow**.
2. Выберите default-ветку с исправленным workflow и запустите.
3. Дождитесь успешного завершения всех шагов. В проверке версии должен быть `pg_dump 17.x`.
4. Откройте запуск → **Artifacts** → скачайте `filet-pattern-postgres-<run_id>`.
5. Распакуйте ZIP. Внутри должен быть `filet-pattern-<run_id>.sql.gz.enc`.

Копирование запланировано ежедневно на 01:17 UTC (04:17 по Москве).
GitHub может задерживать запуск по расписанию. Artifacts хранятся 30 дней;
нужные долгосрочные копии скачивайте отдельно. Для публичного репозитория
GitHub отключает scheduled workflows после 60 дней без активности.
Следите за неуспешными запусками и наличием свежих копий.

## 4. Создать пустую БД для проверки

В DBeaver на подключении к Neon выполните **отдельно, вне транзакции**:

```sql
CREATE DATABASE filet_pattern_restore_test;
```

Если такая БД уже существует, выберите новое имя — не восстанавливайте поверх
предыдущей попытки. Используйте роль с правом создания БД (владельца из Neon).
В Neon Connect выберите созданную БД и скопируйте её direct connection string.
Проверьте, что в URL после hostname указана именно `filet_pattern_restore_test`.
Не запускайте миграции на этой БД до восстановления: архив содержит схему и данные.

## 5. Расшифровать и восстановить

Нужны запущенный Docker Desktop, OpenSSL с поддержкой PBKDF2 и gzip.
В терминале перейдите в каталог с распакованным `.enc` файлом. Откройте Bash:

```sh
bash
```

Вводите следующие блоки по очереди. Значения секретов вводятся скрыто по запросу,
а не записываются в команды истории. Замените имя файла на скачанное:

```bash
set -euo pipefail
umask 077
read -r -s -p 'Пароль шифрования BACKUP_PASSWORD: ' BACKUP_PASSWORD
echo
export BACKUP_PASSWORD
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -pass env:BACKUP_PASSWORD \
  -in 'filet-pattern-<run_id>.sql.gz.enc' -out restore.sql.gz
gzip -t restore.sql.gz
gzip -dc restore.sql.gz > restore.sql
unset BACKUP_PASSWORD
```

Продолжайте только если расшифровка и проверка gzip прошли без ошибок.
Секрет подключения ниже — **строка новой тестовой БД**, не production:

```bash
read -r -s -p 'Connection string тестовой БД: ' PGDATABASE
echo
export PGDATABASE
docker run --rm -e PGDATABASE postgres:17-bookworm \
  psql -X -v ON_ERROR_STOP=1 \
  -c 'SELECT current_database();' -c '\dt'
```

В ответе должно быть `filet_pattern_restore_test` и отсутствие таблиц.
Если указана другая БД или есть таблицы, остановитесь и исправьте подключение.

```bash
docker run --rm -i -e PGDATABASE postgres:17-bookworm \
  psql -X -v ON_ERROR_STOP=1 --single-transaction < restore.sql
docker run --rm -e PGDATABASE postgres:17-bookworm \
  psql -X -v ON_ERROR_STOP=1 -c '\dt' \
  -c 'SELECT version_num FROM alembic_version;' \
  -c "SELECT 'patterns' AS table_name, count(*) FROM patterns
      UNION ALL SELECT 'categories', count(*) FROM categories
      UNION ALL SELECT 'tags', count(*) FROM tags;"
unset PGDATABASE
```

`ON_ERROR_STOP` останавливает восстановление при SQL-ошибке;
`--single-transaction` откатывает изменения при неуспехе.
Используется `psql`, поскольку копия содержит обычный SQL, а не custom-архив `pg_restore`.

## 6. Проверить результат

В DBeaver создайте подключение к тестовой БД с теми же hostname/ролью/SSL,
но с Database = `filet_pattern_restore_test`.

- Сравните набор таблиц, `alembic_version` и числа записей с рабочей БД.
- Откройте несколько паттернов и сравните их содержимое с исходными записями.
- Учитывайте: архив отражает момент копирования. Если рабочая БД менялась после
  выгрузки, более поздние записи в восстановленную копию не попадут.
- Зафиксируйте дату проверки, номер GitHub Actions run и результат сравнения.

Пункт готов после успешного ручного workflow **и** восстановления его artifact
с проверкой данных. Убедитесь также, что следующий запуск по расписанию состоялся.
Рабочее приложение продолжает использовать прежнюю БД; Railway менять не нужно.
После проверки удалите локальные расшифрованные `restore.sql`/`restore.sql.gz`,
если больше не нужны. Зашифрованный архив и пароль храните раздельно.

## Источники

- [GitHub: Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [GitHub: ручной запуск workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [GitHub: schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [PostgreSQL 17: pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html)
