# -*- coding: utf-8 -*-

from . import (
    examples,
    index,
    moteur,
    operateur,
    reference,
    stats,
)


def init_app(app):
    app.register_blueprint(index.mod)
    app.register_blueprint(moteur.mod)
    app.register_blueprint(operateur.mod)
    app.register_blueprint(reference.mod)
    app.register_blueprint(examples.mod)
    app.register_blueprint(stats.mod)
