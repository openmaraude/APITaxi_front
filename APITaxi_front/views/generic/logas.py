"""Generic views for the LogAs feature."""

import json

from flask import abort, current_app, redirect, render_template, request, Response, url_for
import flask_login
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

    logas_sessions is a cookie which stores a list of sessions.

    On log-as, current user's session is prepended to the list logas_sessions.
    On logout, the session is poped from logas_sessions to login as the user.
    """
    cookie_name = 'logas_sessions'

    def store_logas_sessions(self, response, logas_sessions):
        """Store the list of `logas_sessions` in the response cookie
        `cookie_name`.
        """
        if not logas_sessions:
            response.delete_cookie(self.cookie_name)
        else:
            response.set_cookie(self.cookie_name, json.dumps(logas_sessions))

    def get_logas_sessions(self):
        """Load list of logas sessions stored in the request cookie
        `cookie_name`."""
        value = request.cookies.get(self.cookie_name)
        if not value:
            return []
        # Value has been crafted and is not JSON: assume it is empty.
        try:
            logas_sessions = json.loads(value)
        except json.decoder.JSONDecodeError:
            return []
        # Value is JSON but has been crafted and is not a list: assume it is
        # empty.
        if not isinstance(logas_sessions, list):
            return []

        return logas_sessions

    def get_current_session(self):
        """Get the value of flask_login remember_token. On logas, this value is
        saved. On logout, we use
        flask_login.login_maanger._load_user_from_remember_cookie() to login.
        """
        remember_cookie_name = current_app.config.get(
            'REMEMBER_COOKIE_NAME', flask_login.COOKIE_NAME
        )
        ret = request.cookies.get(remember_cookie_name)
        return ret


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
        - store the current user session in cookie
        - login as the User
        """
        form = LogAsForm()

        if form.validate_on_submit():
            query = self.get_users_query()
            user = self.get_user(query, form.user_id.data)

            if not user:
                abort(Response('Invalid user', status=404))

            response = redirect(self.get_redirect_on_success())

            # Prepend current remember_token in the list of logas_sessions.
            logas_sessions = self.get_logas_sessions()
            current_session = self.get_current_session()
            self.store_logas_sessions(response, [current_session] + logas_sessions)

            # Login as the new user, and update the response cookie.
            login_user(user)
            current_app.login_manager._set_cookie(response)

            return response

        return render_template(self.template_name, logas_form=form)


class LogoutAsView(View, LogAsCookieMixin, LogAsRedirectMixin, LogAsSQLAUserMixin):

    def dispatch_request(self):
        """If there is no session stored in cookie, simple logout.

        Otherwise, pop the first session id from the list and identify as the
        user with this session.
        """
        form = FlaskForm()
        if not form.validate_on_submit():
            return redirect('/')

        logas_sessions = self.get_logas_sessions()
        if not logas_sessions:
            return flask_security.views.logout()

        last_logas_session = logas_sessions.pop(0)
        user = current_app.login_manager._load_user_from_remember_cookie(last_logas_session)

        if not user:
            response = flask_security.views.logout()
        else:
            response = redirect(self.get_redirect_on_success())
            login_user(user)

        # last_logas_session has been poped from logas_sessions. Save the
        # cookie in response.
        self.store_logas_sessions(response, logas_sessions)

        return response
