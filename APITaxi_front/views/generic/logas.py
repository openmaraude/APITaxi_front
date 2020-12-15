"""Generic views for the LogAs feature."""

import json

import flask
from flask import abort, current_app, redirect, render_template, request, Response, url_for
from flask_login import login_user
import flask_security
from flask.views import View
from flask_wtf import FlaskForm
import itsdangerous
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


class LogAsRedirectMixin:
    """Mixin to redirect user when logas or logout is successful."""
    redirect_on_success = None

    def get_redirect_on_success(self):
        if self.redirect_on_success:
            return url_for(self.redirect_on_success)
        return '/'


class LogAsSQLAUserMixin:
    user_model = None

    def get_users_query(self):
        """List users. Returns <user_model>.query by default, which returns all
        users.

        To only allow log-as to a subset of users, return a filtered query."""
        if not self.user_model:
            raise NotImplementedError('You should override user_model or get_users_query()')
        return self.user_model.query

    def get_user(self, query, user_id):
        """Given a query on the user model, get the user instance."""
        return query.filter_by(id=user_id).one_or_none()


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

            # Prepend current session in the list of logas_sessions.
            logas_sessions = self.get_logas_sessions()
            signed_session = current_app.session_interface.get_signing_serializer(current_app).dumps(
                dict(flask.session)
            )
            self.store_logas_sessions(response, [signed_session] + logas_sessions)

            login_user(user)

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

        signed_last_logas_session = logas_sessions.pop(0)

        try:
            last_logas_session = current_app.session_interface.get_signing_serializer(
                current_app
            ).loads(signed_last_logas_session)
        # Cookie has been tampered. Remove all logas sessions, and logout user.
        except itsdangerous.exc.BadSignature:
            response = flask_security.views.logout()
            self.store_logas_sessions(response, [])
            return response

        user = self.get_user(self.get_users_query(), last_logas_session['_user_id'])
        # Cookie is valid, but user has been deleted. Remove all logas sessions
        # and logout user.
        if not user:
            response = flask_security.views.logout()
            self.store_logas_sessions(response, [])
            return response

        response = redirect(self.get_redirect_on_success())
        # Remove last_logas_session from list of saved sessions.
        self.store_logas_sessions(response, logas_sessions)

        login_user(user)

        return response
