install:
	pip install -e ".[dev]"

test:
	pytest -q

run:
	uvicorn nexum_core.api.app:app --reload

health:
	curl http://127.0.0.1:8000/health
