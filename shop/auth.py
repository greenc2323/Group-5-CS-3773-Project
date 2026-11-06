"""Alex V.: account creation, password verification and sessions."""
from functools import wraps
import re
import uuid
from botocore.exceptions import ClientError
from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from .db import table

bp = Blueprint('auth', __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not 1 <= len(name) <= 80 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 254 or not 12 <= len(password) <= 128:
            flash('Enter a name, valid email, and a password of 12–128 characters.')
        else:
            try:
                table('users').put_item(Item={'email': email, 'user_id': str(uuid.uuid4()),
                    'name': name, 'password_hash': generate_password_hash(password), 'role': 'customer'},
                    ConditionExpression='attribute_not_exists(email)')
            except ClientError as exc:
                if exc.response['Error']['Code'] != 'ConditionalCheckFailedException':
                    raise
                flash('Unable to register this email. Try signing in.')
            else:
                flash('Account created. Please sign in.')
                return redirect(url_for('auth.login'))
    return render_template('auth.html', register=True)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = table('users').get_item(Key={'email': email or '-'}, ConsistentRead=True).get('Item')
        if user and len(password) <= 128 and check_password_hash(user['password_hash'], password):
            session.clear()
            session['email'] = email
            session.permanent = True
            return redirect(url_for('catalog.index'))
        flash('Email or password is incorrect.')
    return render_template('auth.html', register=False)


@bp.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('catalog.index'))


def save_name(email, name):
    name = name.strip()
    if not email or not 1 <= len(name) <= 80:
        abort(400, description='Enter a name between 1 and 80 characters.')
    try:
        table('users').update_item(Key={'email': email}, UpdateExpression='SET #n = :name',
            ExpressionAttributeNames={'#n': 'name'}, ExpressionAttributeValues={':name': name},
            ConditionExpression='attribute_exists(email)')
    except ClientError as error:
        if error.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise
        abort(404)


@bp.route('/account', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        save_name(g.user['email'], request.form.get('name', ''))
        flash('Account updated.')
        return redirect(url_for('auth.profile'))
    return render_template('profile.html')
