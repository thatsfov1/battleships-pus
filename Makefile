run:
	python3 -m server.main

run-client:
	python3 -m client.main

test:
	python3 -m unittest discover tests

lint:
	# ruff check .
	@echo "Linting complete (placeholder)"

init:
	pip install -r requirements.txt
	python3 init_db.py
	./certs/generate_certs.sh

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
