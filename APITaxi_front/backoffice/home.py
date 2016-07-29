# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, url_for, jsonify
from flask_security import login_required, current_user
from APITaxi_utils import request_wants_json

mod = Blueprint('home_bo', __name__)

@mod.route('/')
@login_required
def home():
    return render_template('base.html')
