import dateutil.parser
import os
import importlib
import json
import pkgutil

from flask import Flask
from flask_redis import FlaskRedis
from flask_security import Security, SQLAlchemyUserDatastore
from flask_wtf import FlaskForm
from sqlalchemy.orm import joinedload

import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration

from APITaxi_models2 import db, Role, User

from . import views


__author__ = 'Vincent Lara'
__contact__ = 'vincent.lara@data.gouv.fr'
__homepage__ = 'https://github.com/'
__version__ = '0.1.0'
__doc__ = 'Frontend of api.taxi'


def jinja2_json_filter(value, indent=2):
    """Jinja template filter to render a JSON string with nice indentation."""
    try:
        content = json.loads(value)
    except json.decoder.JSONDecodeError:
        return value
    # If value is not a string (for example if it is a dict), silently pass the
    # json.loads().
    except TypeError:
        content = value
    return json.dumps(content, indent=indent)


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

    sentry_dsn = app.config.get('SENTRY_DSN')
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            # FlaskIntegration and Sqlalchemyintegration are enabled by default.
            integrations=[
                RedisIntegration(),
            ],
            traces_sample_rate=0.01
        )

    app.template_filter('json')(jinja2_json_filter)
    app.template_filter('str_to_datetime')(jinja2_str_to_datetime_filter)

    db.init_app(app)

    app.redis = FlaskRedis(app)

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

        # blueprint_enabled is a function which can be set by the view to tell
        # whether the blueprint should be active or not. By default, blueprint
        # is active.
        blueprint_enabled = getattr(module, 'blueprint_enabled', None)

        if blueprint:
            if not blueprint_enabled or blueprint_enabled(app):
                app.register_blueprint(blueprint)

    # We need an empty logout form on every page, providing CSRF validation
    @app.context_processor
    def logout_form():
        return {'logout_form': FlaskForm()}

    @app.login_manager.user_loader
    def load_user(user_id):
        """Like most of relationships, User.managed has the flag lazy='raise'
        because most of the API code doesn't need to read the attribute.

        The front, however, needs to read it to display the menu, so let's
        joinedload it to make the current_user.managed attribute available.
        """
        return User.query.options(joinedload(User.managed)).get(user_id)

    return app
