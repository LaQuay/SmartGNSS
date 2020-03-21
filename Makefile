NAME=smartgnss
DOCKER_NAME=domhoyvil/$(NAME)
VERSION=1.0.0
DOCKER_NAME_FULL=$(DOCKER_NAME):$(VERSION)
DOCKER_LOCALHOST=$(shell ip addr show docker0 | grep -Po 'inet \K[\d.]+')
DOCKER_VOLUME=$(shell pwd)
DOCKER_VOLUME_REPORTS=$(shell pwd)/reports

clean:
	@find . -iname "*~" | xargs rm 2>/dev/null || true
	@find . -iname "*.pyc" | xargs rm 2>/dev/null || true
	@find . -iname "build" | xargs rm -rf 2>/dev/null || true

build-frontend: clean
	docker image build -t $(DOCKER_NAME_FULL) ./frontend

build-backend: clean
	docker build -t $(DOCKER_NAME_FULL) ./backend

run-frontend: build-frontend
	docker run -it -p 3000:3000 -p 35729:35729 \
	    --name $(NAME)_frontend \
	    -v $(DOCKER_VOLUME)/frontend:/app \
	    --rm $(DOCKER_NAME_FULL) start

run-backend: build-backend
	docker run -it -p 5000:5000 \
	    --add-host postgres:$(DOCKER_LOCALHOST) \
	    --name $(NAME)_backend \
	    --env-file backend/ENV/api.env --rm $(DOCKER_NAME_FULL)

setup:
	docker-compose -f docker-compose.yml up -d
	@sleep 1
	@sh backend/scripts/configure_postgres.sh smartgnss_postgres_1 api_db
