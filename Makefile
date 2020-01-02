VERSION = $(shell sed -En "s/^__version__[[:blank:]]*=[[:blank:]]*['\"]([0-9\.]+)['\"]/\\1/p" APITaxi_front/__init__.py)

all:
	@echo "To build and push Docker image, run make release"
	@echo "Do not forget to update __version__"

release:
	docker build -t openmaraude/api_taxi_front:${VERSION} -t openmaraude/api_taxi_front:latest .
	docker push openmaraude/api_taxi_front:${VERSION}
	docker push openmaraude/api_taxi_front:latest
