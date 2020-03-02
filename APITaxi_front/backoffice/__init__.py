# -*- coding: utf-8 -*-

from . import (
    admin,
    ads,
    drivers,
    hails,
    home,
    profile,
    user_key,
    zupc,
)


def init_app(app):
    app.register_blueprint(admin.blueprint)
    app.register_blueprint(ads.mod)
    app.register_blueprint(drivers.mod)
    app.register_blueprint(hails.mod)
    app.register_blueprint(home.mod)
    app.register_blueprint(profile.mod)
    app.register_blueprint(user_key.mod)
    app.register_blueprint(zupc.mod)
