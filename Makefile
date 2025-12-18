PYTHON ?= venv/bin/python

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

smoke:
	$(PYTHON) scripts/smoke_test.py

test:
	PYTHONPATH=backend venv/bin/python -m pytest backend/tests

test-strict:
	PYTHONWARNINGS=error PYTHONPATH=backend venv/bin/python -m pytest -q

fmt:
	black backend bot scripts && isort backend bot scripts

migrate:
	cd backend && alembic upgrade head

release-check:
	$(MAKE) test
	docker build -t hr-autopilot-backend-test ./backend
	PYTHONPATH=backend $(PYTHON) scripts/smoke_test.py
