build-image:
	docker build -f Dockerfile . -t sms_api_facade

lint:
	docker compose run --rm lint

start:
	docker compose run --rm bot

stop:
	docker-compose kill -s SIGINT



