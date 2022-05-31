python := $(py) python
addons_dir := addons
support_dir := support

code_path := $(addons_dir) $(support_dir) main.py config.py

reformat:
	$(py) black $(code_path)
	$(py) isort $(code_path)

push:
	git remote | xargs -L1 git push --all

build:
	docker build --pull --rm -f "Dockerfile" -t craftbot:latest .

restart:
	docker build --pull --rm -f "Dockerfile" -t craftbot:latest .
	docker-compose -f "docker-compose-prod.yml" up -d --build
