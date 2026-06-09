# Interpreter Pythona. Na Linux/Mac zwykle 'python3', na Windows 'python'.
# Nadpisz przy wywolaniu, np.:  make run PYTHON=python
PYTHON ?= python3

run:
	$(PYTHON) -m server.main

run-client:
	$(PYTHON) -m client.main

gateway:
	$(PYTHON) ws_gateway.py

# Uruchamia caly stos webowy jedna komenda: serwer gry + most WS + dev server React.
# Serwer i most ida w tle; Ctrl+C zatrzymuje dev server, a 'trap' ubija procesy w tle.
# (Linux/Mac. Na Windows uzyj: powershell -ExecutionPolicy Bypass -File run-all.ps1)
run-all:
	@trap 'kill 0' EXIT; \
	python3 -m server.main & \
	sleep 1; \
	python3 ws_gateway.py & \
	cd web && npm run dev

test:
	$(PYTHON) -m unittest discover tests

lint:
	# ruff check .
	@echo "Linting complete (placeholder)"

init:
	pip install -r requirements.txt
	$(PYTHON) init_db.py
	./certs/generate_certs.sh

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
