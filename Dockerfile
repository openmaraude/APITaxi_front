FROM ubuntu

ARG API_TAXI_MODELS_URL=https://github.com/openmaraude/APITaxi_models
ARG API_TAXI_MODELS_COMMIT=master

ARG API_TAXI_UTILS_URL=https://github.com/openmaraude/APITaxi_utils
ARG API_TAXI_UTILS_COMMIT=master

RUN apt-get update && apt-get install -y \
  libpq-dev \
  python3-pip \
  uwsgi \
  uwsgi-plugin-python3

RUN useradd front

RUN mkdir -p /var/run/api-taxi-front
RUN chown front:front /var/run/api-taxi-front

# ADD detects if file has changed. If we instead ran pip3 install <url>, docker
# would use the cache even if the file has changed.
ADD ${API_TAXI_MODELS_URL}/archive/${API_TAXI_MODELS_COMMIT}.tar.gz /tmp/api_taxi_models.tar.gz
RUN pip3 install /tmp/api_taxi_models.tar.gz
RUN rm -rf /tmp/api_taxi_models.tar.gz

ADD ${API_TAXI_UTILS_URL}/archive/${API_TAXI_UTILS_COMMIT}.tar.gz /tmp/api_taxi_utils.tar.gz
RUN pip3 install /tmp/api_taxi_utils.tar.gz
RUN rm -rf /tmp/api_taxi_utils.tar.gz

COPY . /app
WORKDIR /app

RUN pip3 install .

USER front

CMD ["uwsgi", "/uwsgi.ini"]
