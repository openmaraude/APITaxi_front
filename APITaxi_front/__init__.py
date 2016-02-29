# -*- coding: utf-8 -*-
VERSION = (0, 1, 0)
__author__ = 'Vincent Lara'
__contact__ = "vincent.lara@data.gouv.fr"
__homepage__ = "https://github.com/"
__version__ = ".".join(map(str, VERSION))
__doc__ = "Frontend of api.taxi"

def create_app(sqlalchemy_uri=None):
    from flask import Flask, request_started, request, request_finished, g
    from flask_bootstrap import Bootstrap
    import os

    app = Flask(__name__)
    app.config.from_object('APITaxi_front.default_settings')
    if 'APITAXI_CONFIG_FILE' in os.environ:
        app.config.from_envvar('APITAXI_CONFIG_FILE')
    if not 'ENV' in app.config:
        app.logger.error('ENV is needed in the configuration')
        return None
    if app.config['ENV'] not in ('PROD', 'STAGING', 'DEV'):
        app.logger.error("""Here are the possible values for conf['ENV']:
        ('PROD', 'STAGING', 'DEV') your's is: {}""".format(app.config['env']))
        return None
    #Load configuration from environment variables
    for k in app.config.keys():
        if not k in os.environ:
            continue
        app.config[k] = os.environ[k]
    if sqlalchemy_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_uri

    from APITaxi_models import db
    db.init_app(app)
    from . import backoffice
    backoffice.init_app(app)
    from . import documentation
    documentation.init_app(app)
    Bootstrap(app)

    from APITaxi_utils.version import check_version, add_version_header
    request_started.connect(check_version, app)
    request_finished.connect(add_version_header, app)

    from flask.ext.uploads import configure_uploads
    from .extensions import images
    configure_uploads(app, (images))
    from APITaxi_utils.login_manager import init_app as init_login_manager
    from .backoffice.forms.login import LoginForm

    from .extensions import user_datastore
    init_login_manager(app, user_datastore, LoginForm)
    from . import demo
    demo.create_app(app)

    from APITaxi_models import security
    user_datastore.init_app(db, security.User, security.CachedUser,
            security.Role)

    return app
