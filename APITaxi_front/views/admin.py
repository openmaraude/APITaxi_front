# -*- coding: utf-8 -*-

from flask import abort, Blueprint, redirect, render_template, request, Response, url_for
from flask_login import login_user
import flask_security
from flask_security import current_user, login_required, roles_accepted
from flask_wtf import FlaskForm
from wtforms import IntegerField

from APITaxi_models.security import User


blueprint = Blueprint('admin', __name__)


@blueprint.route('/admin', methods=['GET'])
@login_required
@roles_accepted('admin')
def index():
    return redirect(url_for('admin.logas'))


class LogAsForm(FlaskForm):
    user_id = IntegerField()


@blueprint.route('/admin/logas', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def logas():
    """List users. If POST and user_id is submitted, save the current API key
    in cookie and login as the user."""
    form = LogAsForm()

    if form.validate_on_submit():
        user = User.query.get(form.user_id.data)
        if not user:
            abort(Response('Invalid user', status=404))

        response = redirect(url_for('home.home'))
        response.set_cookie('logas_real_api_key', current_user.apikey)

        login_user(user)
        return response

    return render_template(
        'admin/logas.html',
        logas_form=form
    )


@blueprint.route('/logas/logout')
def logas_logout():
    """Logout user. This endpoint should be called instead of flask_security.views.logout.

    If the user is logged with the "logas" feature, we attempt to reconnect the user back to his previous session.
    """
    logas_api_key = request.cookies.get('logas_real_api_key')

    if logas_api_key:
        user = User.query.filter(User.apikey == logas_api_key).first()
        if not user:  # bad API key
            response = flask_security.views.logout()
        else:
            response = redirect(url_for('admin.logas'))
            login_user(user)

        response.delete_cookie('logas_real_api_key')
        return response

    return flask_security.views.logout()
