# -*- coding: utf-8 -*-
import APITaxi_models import models
from .forms.administrative import ZUPCreateForm, ZUPCUpdateForm
from APITaxi_utils.request_wants_json import request_wants_json
from flask_security import login_required, roles_accepted, current_user
from flask_restplus import reqparse, marshal
from flask import (Blueprint, request, render_template, redirect, jsonify,
                   url_for, current_app)
from psycopg2.extras import RealDictCursor


mod = Blueprint('zupc', __name__)

@mod.route('/zupc/_view')
def zupc():
    if request.method != "GET":
        abort(405, message="method now allowed")
    if request_wants_json():
        abort(400, message="bad format")
    roles_accepted = set(['admin', 'mairie', 'prefecture', 'operateur'])
    if  current_user.is_anonymous() or\
            len(roles_accepted.intersection(current_user.roles)) == 0:
        abort(403)
    page = int(request.args.get('page')) if 'page' in request.args else 1
    return render_template('lists/zupc.html',
        zupc_list=models.ZUPC.query.paginate(page))


@mod.route('/zupc/form', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin', 'mairie', 'prefecture')
def zupc_form():
    form = None
    if request.args.get("id"):
        zupc = models.ZUPC.query.get(request.args.get("id"))
        if not zupc:
            abort(404, message="Unable to find ZUPC")
        form = ZUPCUpdateForm(obj=zupc)
    else:
        form = ZUPCreateForm()
    if request.method == "POST":
        if request.args.get("id"):
            form.populate_obj(zupc)
            if form.validate():
                current_app.extensions['sqlalchemy'].db.session.commit()
                return redirect(url_for('zupc.zupc'))
        else:
            if form.validate():
                zupc = models.ZUPC()
                form.populate_obj(zupc)
                current_app.extensions['sqlalchemy'].db.session.add(zupc)
                current_app.extensions['sqlalchemy'].db.session.commit()
                return redirect(url_for('zupc.zupc'))
    return render_template('forms/ads.html', form=form,
        form_method="POST", submit_value="Modifier")


@mod.route('/zupc/delete')
@login_required
@roles_accepted('admin', 'mairie', 'prefecture')
def zupc_delete():
    if not request.args.get("id"):
        abort(404, message="id is required")
    zupc = models.ZUPC.query.get(request.args.get("id"))
    if not zupc:
        abort(404, message="Unable to find the ZUPC")
    current_app.extensions['sqlalchemy'].db.session.delete(zupc)
    current_app.extensions['sqlalchemy'].db.session.commit()
    return redirect(url_for("zupc.zupc"))


@mod.route('/zupc/autocomplete')
def zupc_autocomplete():
    #@TODO: have some identification here?
    term = request.args.get('q')
    like = "%{}%".format(term)

    response = models.ZUPC.query.filter(
            models.ZUPC.nom.ilike(like)).all()
    return jsonify(suggestions=map(lambda zupc:{'name': zupc.nom, 'id': int(zupc.id)},
                                        response))

@mod.route('/zupc/_show_temp')
def zupc_show_temp():
    cur = current_app.extensions['sqlalchemy'].db.session.connection().\
            connection.cursor(cursor_factory=RealDictCursor)
    cur.execute("""SELECT id, nom, insee FROM zupc_temp 
                   WHERE multiple=true AND parent_id = id;""")

    return render_template("zupc_show_temp.html",
                          list_zupc=cur.fetchall(),
                          apikey=current_user.apikey,
                          mapbox_token=current_app.config['MAPBOX_TOKEN'])


