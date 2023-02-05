python := $(py) python

code_path := src

reformat:
	$(py) black $(code_path)
	$(py) isort $(code_path)

restart:
	docker build --pull --rm -f "Dockerfile" -t craftbot:latest .
	docker-compose -f "docker-compose-prod.yml" up -d --build

stop:
	docker-compose -f "docker-compose-prod.yml" down
