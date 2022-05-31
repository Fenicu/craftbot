# Установка в докер на примере Ubuntu 21.10

## Установка докера
```bash
sudo apt update

sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"

sudo apt update

sudo apt install -y docker-ce

sudo usermod -aG docker ${USER}

su - ${USER}```

## Установка docker compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose```

## Сбилдить образ бота и запустить
```bash
docker build --pull --rm -f "Dockerfile" -t craftbot:latest "."

docker-compose -f "docker-compose.yml" up -d --build```


# Установка для разработки

## Установка баз данных в докер
```bash
docker run -p127.0.0.1:27017:27017 --restart=always --name mongo-server -d mongo:4.2

docker run -p127.0.0.1:6379:6379 --restart=always --name redis-server -d redis:latest```

## Установка python
```bash
sudo apt install software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa

sudo apt update

sudo apt install python3.9```

## Установка зависимостей
```bash
python3.9 -m pip install virtualenv

python3.9 -m venv env

source ./env/bin/activate

pip install -r requirements.txt```

Добавить в .bashrc

```bash
function __envfile {
       set -o allexport
       [[ -f ${1} ]] && source ${1}
       set +o allexport
}
alias envfile='__envfile'
```

Создать свой .env файл на примере example.env и экспортировать настройки в переменные окружения

`envfile .env`

Запустить бота из src
```bash
cd ./src

python main.py```
