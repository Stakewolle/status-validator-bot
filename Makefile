install:
	pip install -r requirements.txt
test:
	docker-compose build && docker-compose start

run:
	docker build -t cosmos_exporter:latest . &&  docker run -d --restart unless-stopped -p 8001:8001 --network="host" cosmos_exporter:latest