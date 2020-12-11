"""Generic views for the LogAs feature."""

import json

from flask import abort, redirect, render_template, request, Response
from flask_login import login_user
import flask_security
from flask_security import current_user
from flask.views import View
from flask_wtf import FlaskForm
from wtforms import IntegerField


class LogAsForm(FlaskForm):
    user_id = IntegerField()


def set_logas_cookie(response, logas_api_keys):
    if not logas_api_keys:
        response.delete_cookie('logas_real_api_key')
    else:
        response.set_cookie('logas_real_api_key', json.dumps(logas_api_keys))


def load_logas_cookie(cookies):
    value = cookies.get('logas_real_api_key')
    if not value:
        return []
    try:
        keys = json.loads(value)
    except json.decoder.JSONDecodeError:
        return []

    if not isinstance(keys, list):
        return []

    return keys


class LogAsView(View):

    user_model = None
    template_name = None
    redirect_on_success = '/'

    def get_redirect_on_success(self):
        return self.redirect_on_success

    def get_template_name(self):
        """Template to render."""
        if not self.template_name:
            raise NotImplementedError('You should override template_name or get_template_name()')
        return self.template_name

    def get_users_query(self):
        """Override to specify the query to limit the users possible to log as."""
        if not self.user_model:
            raise NotImplementedError('You should override user_model or get_users_query()')
        return self.user_model.query

    def get_user(self, query, user_id):
        """Given a query on the user model, get the user instance."""
        return query.filter_by(id=user_id).one_or_none()

    def dispatch_request(self):

        form = LogAsForm()

        if form.validate_on_submit():
            query = self.get_users_query()
            user = self.get_user(query, form.user_id.data)

            if not user:
                abort(Response('Invalid user', status=404))

            response = redirect(self.get_redirect_on_success())
            set_logas_cookie(response, [current_user.apikey] + load_logas_cookie(request.cookies))

            login_user(user)
            return response

        return render_template(self.get_template_name(), logas_form=form)


class LogoutAsView(View):

    redirect_on_success = '/'
    user_model = None

    def get_redirect_on_success(self):
        return self.redirect_on_success

    def get_user_model(self):
        if not self.user_model:
            raise NotImplementedError('You should override user_model or get_user_model()')
        return self.user_model

    def dispatch_request(self):
        form = FlaskForm()
        if not form.validate_on_submit():
            return redirect('/')

        logas_api_keys = load_logas_cookie(request.cookies)
        if not logas_api_keys:
            return flask_security.views.logout()

        user = self.get_user_model().query.filter_by(apikey=logas_api_keys[0]).first()
        if not user:  # bad API key
            response = flask_security.views.logout()
        else:
            response = redirect(self.get_redirect_on_success())
            login_user(user)

        logas_api_keys.pop(0)
        set_logas_cookie(response, logas_api_keys)

        return response
