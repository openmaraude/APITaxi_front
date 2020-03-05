# -*- coding: utf-8 -*-

from . import (
    admin,
    ads,
    dashboards,
    drivers,
    hails,
    home,
    profile,
    zupc,
)


def init_app(app):
    app.register_blueprint(admin.blueprint)
    app.register_blueprint(ads.mod)
    app.register_blueprint(dashboards.blueprint)
    app.register_blueprint(drivers.mod)
    app.register_blueprint(hails.mod)
    app.register_blueprint(home.blueprint)
    app.register_blueprint(profile.blueprint)
    app.register_blueprint(zupc.mod)
