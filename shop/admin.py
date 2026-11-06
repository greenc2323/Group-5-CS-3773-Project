"""Staff tools for the catalog, promotions, customers, and orders."""
from functools import wraps
import re
import uuid
from urllib.parse import urlsplit

from botocore.exceptions import ClientError
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .auth import login_required, save_name
from .db import all_items, table

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(view):
    @wraps(view)
    @login_required
    def protected(*args, **kwargs):
        if g.user.get('role') != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return protected


@bp.get('/')
@admin_required
def index():
    users = all_items(table('users'), ProjectionExpression='email, user_id, #n, #r',
                      ExpressionAttributeNames={'#n': 'name', '#r': 'role'})
    names = {user['user_id']: user['email'] for user in users}
    orders = all_items(table('orders'))
    for order in orders:
        order['customer'] = order.get('customer_email', names.get(order['user_id'], order['user_id']))
    sort = request.args.get('sort', 'date')
    keys = {'date': lambda o: o['created_at'], 'customer': lambda o: o['customer'],
            'total': lambda o: o['total_cents']}
    orders.sort(key=keys.get(sort, keys['date']), reverse=sort != 'customer')
    return render_template('admin.html', products=all_items(table('products')),
                           discounts=all_items(table('discounts')), users=users, orders=orders, sort=sort)


@bp.post('/products')
@admin_required
def product():
    pid = request.form.get('product_id') or uuid.uuid4().hex
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()
    image_url = request.form.get('image_url', '').strip()
    try:
        price = int(request.form['price_cents'])
        stock = int(request.form['stock'])
        sale = int(request.form.get('sale_cents') or 0)
        version = int(request.form.get('version') or 0)
        image = urlsplit(image_url)
    except (ValueError, KeyError):
        abort(400, description='Enter valid prices in cents and a whole-number stock count.')
    if not (1 <= len(name) <= 100 and 1 <= len(description) <= 500 and 1 <= len(category) <= 60
            and 0 < price <= 10000000 and 0 <= sale < price and 0 <= stock <= 100000
            and (not image_url or (image.scheme == 'https' and image.hostname and len(image_url) <= 500))):
        abort(400, description='Check the product details, prices, stock, and HTTPS image URL.')
    item = dict(product_id=pid, name=name, description=description, category=category,
                price_cents=price, stock=stock, sale_cents=sale, image_url=image_url, version=version + 1)
    if request.form.get('product_id'):
        condition = 'attribute_exists(product_id) AND #ver = :v'
        if version == 0:
            condition = 'attribute_exists(product_id) AND attribute_not_exists(#ver)'
        kwargs = {'ExpressionAttributeNames': {'#ver': 'version'}}
        if version:
            kwargs['ExpressionAttributeValues'] = {':v': version}
    else:
        condition, kwargs = 'attribute_not_exists(product_id)', {}
    try:
        table('products').put_item(Item=item, ConditionExpression=condition, **kwargs)
    except ClientError as error:
        if error.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise
        flash('Product changed. Review the latest values before saving.')
    return redirect(url_for('admin.index'))


@bp.post('/discounts')
@admin_required
def discount():
    code = request.form.get('code', '').strip().upper()
    try:
        percent = int(request.form['percent'])
    except (ValueError, KeyError):
        abort(400, description='Enter a whole percentage.')
    if not re.fullmatch(r'[A-Z0-9-]{1,24}', code) or not 1 <= percent <= 100:
        abort(400, description='Use a code of up to 24 letters, numbers or hyphens and a percent from 1 to 100.')
    table('discounts').put_item(Item={'code': code, 'percent': percent})
    return redirect(url_for('admin.index'))


@bp.post('/users')
@admin_required
def user():
    save_name(request.form.get('email', ''), request.form.get('name', ''))
    return redirect(url_for('admin.index'))


@bp.post('/orders/complete')
@admin_required
def complete():
    table('orders').update_item(
        Key={'user_id': request.form['user_id'], 'order_id': request.form['order_id']},
        UpdateExpression='SET fulfillment = :done', ConditionExpression='attribute_exists(order_id)',
        ExpressionAttributeValues={':done': 'completed'})
    return redirect(url_for('admin.index'))
