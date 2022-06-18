python := $(py) python


reformat:
	$(py) black src
	$(py) isort src

push:
	git remote | xargs -L1 git push --all

build:
	docker build --pull --rm -f "Dockerfile" -t craftbot:latest .

restart:
	docker build --pull --rm -f "Dockerfile" -t craftbot:latest .
	docker-compose -f "docker-compose-prod.yml" up -d --build
