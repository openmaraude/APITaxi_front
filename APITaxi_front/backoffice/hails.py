from flask import Blueprint, render_template, request
from flask_security import login_required, roles_accepted, current_user
import APITaxi_models as models

mod = Blueprint('hail', __name__)

@mod.route('/hails/_explore')
@mod.route('/taxis/<string:taxi_id>/hails/_explore')
@login_required
@roles_accepted('admin', 'operateur', 'moteur')
def hails_explore(taxi_id=None):
    if 'id' in request.args:
        return hails_log(request.args['id'])
    operateurs = []
    moteurs = []
    for u in models.security.User.query.all():
        if u.has_role('operateur') and current_user.has_role('admin'):
            operateurs.append(str(u.email))
        if u.has_role('moteur') and current_user.has_role('admin'):
            moteurs.append(str(u.email))
    return render_template('hails.html', apikey=current_user.apikey,
                          statuses=models.hail.status_enum_list, operateurs=operateurs,
                          moteurs=moteurs, taxi_id=taxi_id)


@mod.route('/hails/<string:hail_id>/_explore')
@login_required
@roles_accepted('admin', 'operateur', 'moteur')
def hails_log(hail_id):
    return render_template('hails_log.html',
            apikey=current_user.apikey, hail_id=hail_id)

@mod.route('/hails/_map')
@login_required
@roles_accepted('admin', 'operateur', 'moteur')
def hails_map_list():
    if 'id' in request.args:
        return hails_log(request.args['id'])
    operateurs = []
    moteurs = []
    for u in models.security.User.query.all():
        if u.has_role('operateur') and current_user.has_role('admin'):
            operateurs.append(str(u.email))
        if u.has_role('moteur') and current_user.has_role('admin'):
            moteurs.append(str(u.email))
    return render_template('hails_list_map.html', apikey=current_user.apikey,
                          statuses=models.hail.status_enum_list, operateurs=operateurs,
                          moteurs=moteurs)


@mod.route('/hails/<string:hail_id>/_map')
@login_required
@roles_accepted('admin', 'operateur', 'moteur')
def hails_map(hail_id):
    return render_template('hail_map.html',
            apikey=current_user.apikey, hail_id=hail_id)
