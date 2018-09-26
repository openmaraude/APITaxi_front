# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, current_app
from flask_security import current_user
from ..extensions import user_datastore
import APITaxi_models as models
from functools import partial

mod = Blueprint('examples', __name__)


def make_url(p, *params, **kparams):
    path = current_app.config['SERVER_NAME'] or 'localhost'
    path += p
    if params:
        path += '?'
        path += '&'.join(params)
    elif kparams:
        path += '?'
        path += '&'.join([str(k)+'='+str(v) for k, v in kparams.items()])
    return path

@mod.route('/documentation/examples')
def doc_index():
    if not current_user.is_anonymous:
        apikeys_operator = set()
        apikeys_moteur = set()
        if 'operateur' in current_user.roles:
            apikeys_operator.add(('your token', current_user.apikey))
        if 'moteur' in current_user.roles:
            apikeys_moteur.add(('your token', current_user.apikey))
        apikeys_operator.add(('neotaxi', user_datastore.find_user(email='neotaxi').apikey))
        apikeys_moteur.add(('neomap', user_datastore.find_user(email='neomap').apikey))
        taxis = models.Taxi.query.filter(models.Taxi.added_by==user_datastore.\
                    find_user(email='neotaxi').id).all()
    else:
        apikeys_operator = [('anonymous', 'token')]
        apikeys_moteur = [('anonymous', 'token')]
        taxis = []

    return render_template('documentation/examples.html',
                 apikeys_operator=apikeys_operator,
                 apikeys_moteur=apikeys_moteur,
                 taxis=taxis,
                 make_url=make_url)
