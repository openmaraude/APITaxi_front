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
    """Mixin to manipulate logas cookies.

    logas_secrets is a cookie which stores a list of secrets.

    On log-as, the current user's secret is stored in logas_secrets for later
    retrieval before login.

    On logout, the secret is retrieved from logas_secrets to login user.
    """
    cookie_name = 'logas_secrets'

    def set_logas_cookie(self, response, logas_secrets):
        """Store the list of secrets in response cookie."""
        if not logas_secrets:
            response.delete_cookie(self.cookie_name)
        else:
            response.set_cookie(self.cookie_name, json.dumps(logas_secrets))

    def load_logas_cookie(self):
        """Loads the list of secrets from request cookie."""
        value = request.cookies.get(self.cookie_name)
        if not value:
            return []
        # Value has been crafted and is not JSON: assume it is empty.
        try:
            logas_secrets = json.loads(value)
        except json.decoder.JSONDecodeError:
            return []
        # Value is JSON but has been crafted and is not a list: assume it is
        # empty.
        if not isinstance(logas_secrets, list):
            return []
        return logas_secrets


class LogAsRedirectMixin:
    """Mixin to redirect user when logas or logout is successful."""
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
        """List users. Returns <user_model>.query by default, which returns all
        users.

        To only allow log-as to a subset of users, return a filtered query."""
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
        """For GET requests, return template_name.

        For POST requests:

        - get the User object with the user_id provided
        - store the current user secret in cookie
        - login as the User
        """
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
        """If there is no secret stored in cookie, simple logout.

        Otherwise, pop the first secret from the list of secrets stored in
        cookies, and identify as the user with this secret.
        """
        form = FlaskForm()
        if not form.validate_on_submit():
            return redirect('/')

        logas_secrets = self.load_logas_cookie()
        if not logas_secrets:
            return flask_security.views.logout()

        user_filter = {self.user_secret_attr: logas_secrets[0]}
        user = self.get_users_query().filter_by(**user_filter).first()
        if not user:
            response = flask_security.views.logout()
        else:
            response = redirect(self.get_redirect_on_success())
            login_user(user)

        logas_secrets.pop(0)
        self.set_logas_cookie(response, logas_secrets)

        return response
