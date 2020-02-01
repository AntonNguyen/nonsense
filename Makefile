.PHONY: run

run:
	gunicorn --bind :8080 --reload nonsense.app:app