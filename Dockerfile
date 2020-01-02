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

RUN pip3 install ${API_TAXI_MODELS_URL}/archive/${API_TAXI_MODELS_COMMIT}.tar.gz
RUN pip3 install ${API_TAXI_UTILS_URL}/archive/${API_TAXI_UTILS_COMMIT}.tar.gz

COPY . /app
WORKDIR /app

RUN pip3 install .

USER front

CMD ["uwsgi", "/uwsgi.ini"]
