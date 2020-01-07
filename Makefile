DOCKER_IMAGE = openmaraude/api_taxi_front
VERSION = $(shell sed -En "s/^__version__[[:blank:]]*=[[:blank:]]*['\"]([0-9\.]+)['\"]/\\1/p" APITaxi_front/__init__.py)

all:
	@echo "To build and push Docker image, run make release"
	@echo "Do not forget to update __version__"

release:
	docker build -t ${DOCKER_IMAGE}:${VERSION} -t ${DOCKER_IMAGE}:latest .
	docker push ${DOCKER_IMAGE}:${VERSION}
	docker push ${DOCKER_IMAGE}:latest
