# If True, front is running with the integration mode enabled and a menu is
# added to create taxis and hail them.
INTEGRATION_ENABLED = False

# Account used by the integration feature to query APITaxi.
INTEGRATION_ACCOUNT_EMAIL = None

# Geotaxi is used by the integration feature to update the position of a taxi.
GEOTAXI_HOST = None
GEOTAXI_PORT = None

# Used by integration features.
API_TAXI_URL = None

DEBUG = True
SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/taxis'
REDIS_URL = "redis://:@localhost:6379/0"

# https://flask-security-too.readthedocs.io/en/stable/configuration.html
SECRET_KEY = 'super-secret'
SECURITY_PASSWORD_SALT = 'pepper'

INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USER = ''
INFLUXDB_PASSWORD = ''
INFLUXDB_TAXIS_DB = 'taxis'
INFLUXDB_USE_UDP = False
INFLUXDB_UDP_PORT = 0

# Warning is displayed when SQLALCHEMY_TRACK_MODIFICATIONS is the default.
# Future SQLAlchemy version will set this value to False by default anyway.
SQLALCHEMY_TRACK_MODIFICATIONS = False
