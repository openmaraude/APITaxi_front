# -*- coding: utf-8 -*-

import dateutil
import os
import importlib
import inspect
import json
import pkgutil

from flask import Flask
from flask_redis import FlaskRedis
from flask_security import Security, SQLAlchemyUserDatastore

from APITaxi_models import db
from APITaxi_models.security import User, Role

from . import views


__author__ = 'Vincent Lara'
__contact__ = 'vincent.lara@data.gouv.fr'
__homepage__ = 'https://github.com/'
__version__ = '0.1.0'
__doc__ = 'Frontend of api.taxi'


redis_client = FlaskRedis()


def jinja2_json_filter(value, indent=2):
    """Jinja template filter to render a JSON string with nice indentation."""
    return json.dumps(json.loads(value), indent=indent)


def jinja2_str_to_datetime_filter(value):
    """Jinja template filter to convert a string to a datetime object."""
    return dateutil.parser.parse(value)


def create_app():
    app = Flask(__name__)

    # Load default configuration
    app.config.from_object('APITaxi_front.default_settings')

    # Override default conf with environment variable APITAXI_CONFIG_FILE
    if 'APITAXI_CONFIG_FILE' not in os.environ:
        raise RuntimeError('APITAXI_CONFIG_FILE environment variable required')
    app.config.from_envvar('APITAXI_CONFIG_FILE')

    app.template_filter('json')(jinja2_json_filter)
    app.template_filter('str_to_datetime')(jinja2_str_to_datetime_filter)

    db.init_app(app)

    redis_client.init_app(app)

    # Setup flask-security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(app, user_datastore)

    # Register blueprints dynamically: list all modules in views/ and register
    # blueprint. Blueprint's name must be exactly "blueprint".
    for _imp, modname, _pkg in pkgutil.walk_packages(
        views.__path__, views.__name__ + '.'
    ):
        module = importlib.import_module(modname)
        blueprint = getattr(module, 'blueprint', None)
        if blueprint:
            app.register_blueprint(blueprint)

    return app
