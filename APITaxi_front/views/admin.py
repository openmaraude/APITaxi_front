# -*- coding: utf-8 -*-

from flask import Blueprint, redirect, request, url_for
from flask_login import login_user
import flask_security
from flask_security import login_required, roles_accepted
from flask_wtf import FlaskForm
from wtforms import IntegerField

from APITaxi_models2 import User

from .generic.logas import LogAsView


blueprint = Blueprint('admin', __name__)


@blueprint.route('/admin', methods=['GET'])
@login_required
@roles_accepted('admin')
def index():
    return redirect(url_for('admin.logas'))


class LogAsForm(FlaskForm):
    user_id = IntegerField()


class AdminLogAs(LogAsView):
    """Logas view for administrators. We allow to login as any user, so there
    is no filter on the users_model.
    """
    decorators = [
        login_required,
        roles_accepted('admin')
    ]

    template_name = 'admin/logas.html'
    user_model = User

    def get_redirect_on_success(self):
        return url_for('home.home')


blueprint.add_url_rule(
    '/admin/logas',
    view_func=AdminLogAs.as_view('logas'),
    methods=['GET', 'POST']
)


@blueprint.route('/logas/logout', methods=['POST'])
def logas_logout():
    """Logout user. This endpoint should be called instead of
    flask_security.views.logout.

    If the user is logged with the "logas" feature, we attempt to reconnect the
    user back to his previous session.
    """
    # CSRF Validation
    form = FlaskForm()
    if not form.validate_on_submit():
        # On invalid token, don't do anything
        # redirect to home as we don't have a logout landing page
        return redirect(url_for('home.home'))

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
