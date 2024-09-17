# Установка в докер на примере Ubuntu 21.10

## Установка докера и docker-compose
`sudo bash install-docker.sh`

## Сбилдить образ бота и запустить
Заменить переменные среды в файле docker-compose.yml

```bash
docker-compose -f "docker-compose.yml" up -d --build
```

## Восстановить базу данных
База данных актуальна на 17.09.24 (вышли павербанк и штаны), там лежат все крафты, сеты, тиры и предметы

```bash
bash restore_db.sh
```
