# -*- coding: utf-8 -*-

def init_app(app):
    from APITaxi_models.hail import Hail
    from . import ads, drivers, home, user_key, zupc, profile, hails, admin
    app.register_blueprint(ads.mod)
    app.register_blueprint(drivers.mod)
    app.register_blueprint(home.mod)
    app.register_blueprint(user_key.mod)
    app.register_blueprint(zupc.mod)
    app.register_blueprint(profile.mod)
    app.register_blueprint(hails.mod)
    app.register_blueprint(admin.blueprint)
