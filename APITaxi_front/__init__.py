# -*- coding: utf-8 -*-

import os

from flask import Flask, request_started, request, request_finished, g
from flask_bootstrap import Bootstrap
from flask_uploads import configure_uploads

from APITaxi_models import db
from APITaxi_utils.login_manager import init_app as init_login_manager
from APITaxi_models.security import User, Role

from . import backoffice, documentation
from .backoffice.forms.login import LoginForm
from .extensions import user_datastore


__author__ = 'Vincent Lara'
__contact__ = "vincent.lara@data.gouv.fr"
__homepage__ = "https://github.com/"
__version__ = '0.1.0'
__doc__ = "Frontend of api.taxi"


def create_app():
    app = Flask(__name__)

    # Load default configuration
    app.config.from_object('APITaxi_front.default_settings')

    # Override default conf with environment variable APITAXI_CONFIG_FILE
    if 'APITAXI_CONFIG_FILE' not in os.environ:
        raise RuntimeError('APITAXI_CONFIG_FILE environment variable required')
    app.config.from_envvar('APITAXI_CONFIG_FILE')

    db.init_app(app)

    backoffice.init_app(app)
    documentation.init_app(app)
    Bootstrap(app)

    configure_uploads(app, (backoffice.extensions.images))

    init_login_manager(app, user_datastore, LoginForm)

    user_datastore.init_app(db, User, Role)

    return app
