import functools

from flask import Blueprint, current_app, redirect, url_for
from flask_security import current_user, login_required

from APITaxi_models2 import User

from .generic.logas import LogAsView


blueprint = Blueprint('manager', __name__)


@blueprint.route('/manager', methods=['GET'])
@login_required
def index():
    return redirect(url_for('manager.logas'))


def require_manager(func):
    """Redirect to login page if user is not an account manager."""
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        if current_user.is_authenticated and current_user.managed:
            return func(*args, **kwargs)
        return current_app.login_manager.unauthorized()
    return wrapped


class ManagerLogAs(LogAsView):
    decorators = [
        login_required,
        require_manager
    ]

    template_name = 'manager/logas.html'
    redirect_on_success = 'home.home'

    def get_users_query(self):
        """Only allow logas users managed by this user."""
        return User.query.filter(User.id.in_([user.id for user in current_user.managed]))


blueprint.add_url_rule(
    '/manager/logas',
    view_func=ManagerLogAs.as_view('logas'),
    methods=['GET', 'POST']
)
