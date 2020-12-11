# -*- coding: utf-8 -*-

from flask import Blueprint, redirect, request, url_for
from flask_login import login_user
import flask_security
from flask_security import login_required, roles_accepted
from flask_wtf import FlaskForm
from wtforms import IntegerField

from APITaxi_models2 import User

from .generic.logas import LogAsView, LogoutAsView


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


class Logout(LogoutAsView):

    user_model = User

    def get_redirect_on_success(self):
        return url_for('home.home')


blueprint.add_url_rule(
    '/logas/logout',
    view_func=Logout.as_view('logas_logout'),
    methods=['POST']
)
