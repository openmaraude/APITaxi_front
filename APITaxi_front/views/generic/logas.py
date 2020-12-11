"""Generic views for the LogAs feature."""

import json

from flask import abort, redirect, render_template, request, Response, url_for
from flask_login import login_user
import flask_security
from flask_security import current_user
from flask.views import View
from flask_wtf import FlaskForm
from wtforms import IntegerField


class LogAsForm(FlaskForm):
    user_id = IntegerField()


class LogAsCookieMixin:

    cookie_name = 'logas_real_api_key'

    def set_logas_cookie(self, response, logas_api_keys):
        if not logas_api_keys:
            response.delete_cookie(self.cookie_name)
        else:
            response.set_cookie(self.cookie_name, json.dumps(logas_api_keys))

    def load_logas_cookie(self):
        value = request.cookies.get(self.cookie_name)
        if not value:
            return []
        try:
            keys = json.loads(value)
        except json.decoder.JSONDecodeError:
            return []

        if not isinstance(keys, list):
            return []

        return keys


class LogAsRedirectMixin:

    redirect_on_success = None

    def get_redirect_on_success(self):
        if self.redirect_on_success:
            return url_for(self.redirect_on_success)
        return '/'


class LogAsSQLAUserMixin:

    user_model = None
    user_id_attr = 'id'
    user_secret_attr = 'apikey'

    def get_users_query(self):
        """Override to specify the query to limit the users possible to log as."""
        if not self.user_model:
            raise NotImplementedError('You should override user_model or get_users_query()')
        return self.user_model.query

    def get_user(self, query, user_id):
        """Given a query on the user model, get the user instance."""
        filters = {self.user_id_attr: user_id}
        return query.filter_by(**filters).one_or_none()


class LogAsView(View, LogAsCookieMixin, LogAsRedirectMixin, LogAsSQLAUserMixin):

    template_name = None

    def dispatch_request(self):
        form = LogAsForm()

        if form.validate_on_submit():
            query = self.get_users_query()
            user = self.get_user(query, form.user_id.data)

            if not user:
                abort(Response('Invalid user', status=404))

            response = redirect(self.get_redirect_on_success())
            self.set_logas_cookie(
                response,
                [getattr(current_user, self.user_secret_attr)] + self.load_logas_cookie()
            )

            login_user(user)
            return response

        return render_template(self.template_name, logas_form=form)


class LogoutAsView(View, LogAsCookieMixin, LogAsRedirectMixin, LogAsSQLAUserMixin):

    def dispatch_request(self):
        form = FlaskForm()
        if not form.validate_on_submit():
            return redirect('/')

        logas_api_keys = self.load_logas_cookie()
        if not logas_api_keys:
            return flask_security.views.logout()

        user_filter = {self.user_secret_attr: logas_api_keys[0]}
        user = self.get_users_query().filter_by(**user_filter).first()
        if not user:  # bad API key
            response = flask_security.views.logout()
        else:
            response = redirect(self.get_redirect_on_success())
            login_user(user)

        logas_api_keys.pop(0)
        self.set_logas_cookie(response, logas_api_keys)

        return response
