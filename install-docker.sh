#!/bin/bash

if ! command -v docker &> /dev/null; then
    echo "Docker не установлен. Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    echo "Установка Docker завершена."
    sudo usermod -aG docker $USER
    echo "Текущий пользователь добавлен в группу docker."
else
    echo "Docker уже установлен."
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose не установлен. Установка Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Установка Docker Compose завершена."
else
    echo "Docker Compose уже установлен."
fi
