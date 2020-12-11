"""Generic views for the LogAs feature."""

from flask import abort, redirect, render_template, Response
from flask_login import login_user
from flask_security import current_user
from flask.views import View
from flask_wtf import FlaskForm
from wtforms import IntegerField


class LogAsForm(FlaskForm):
    user_id = IntegerField()


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

    def get_users_model(self):
        """SQLAlchemy User model."""
        return self.user_model

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
            response.set_cookie('logas_real_api_key', current_user.apikey)

            login_user(user)
            return response

        return render_template(self.get_template_name(), logas_form=form)
