from flask import Blueprint, render_template, request
from flask.ext.security import login_required, roles_accepted, current_user

mod = Blueprint('hail', __name__)

@mod.route('/hails/_explore')
@login_required
@roles_accepted('admin', 'operateur', 'moteur')
def hails_explore():
    print request.args
    if 'id' in request.args:
        return hails_log(request.args['id'])
    return render_template('hails.html', apikey=current_user.apikey)


@mod.route('/hails/<string:hail_id>/_explore')
@login_required
@roles_accepted('admin', 'operateur', 'moteur')
def hails_log(hail_id):
    return render_template('hails_log.html',
            apikey=current_user.apikey, hail_id=hail_id)
