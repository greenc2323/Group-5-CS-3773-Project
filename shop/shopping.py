"""Shared integration: server-side cart and atomic, simulated checkout."""
from datetime import datetime, timezone
from hashlib import sha256
import uuid
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from .auth import login_required
from .db import table
from .pricing import quote, unit_price

bp = Blueprint('shopping', __name__)


def read_cart():
    return table('carts').get_item(Key={'user_id': g.user['user_id']}, ConsistentRead=True).get('Item',
        {'user_id': g.user['user_id'], 'items': {}})


def cart_lines(cart, *, preview=False):
    lines = []
    for pid, qty in cart['items'].items():
        product = table('products').get_item(Key={'product_id': pid}, ConsistentRead=True).get('Item')
        if not product and not preview:
            raise ValueError('A product was removed. Remove it from your cart before checkout.')
        product = product or {'name': 'Unavailable product', 'price_cents': 0, 'stock': 0}
        price = unit_price(product)
        lines.append({'product_id': pid, 'name': product['name'], 'price_cents': price,
                      'regular_cents': product['price_cents'], 'version': product.get('version', 0),
                      'quantity': int(qty), 'stock': int(product['stock']), 'subtotal': price * qty})
    return lines


def quote_id(lines, totals):
    prices = sorted((line['product_id'], int(line['price_cents']), line['quantity']) for line in lines)
    values = (prices, totals['discount_code'], totals['discount_percent'], int(totals['total_cents']))
    return sha256(repr(values).encode('utf-8')).hexdigest()


@bp.get('/cart')
@login_required
def cart():
    saved = read_cart()
    lines = cart_lines(saved, preview=True)
    code = saved.get('discount_code', '')
    try:
        totals = quote(lines, code)
        warning = None
    except ValueError as error:
        totals = quote(lines, '')
        warning = str(error)
    return render_template('cart.html', lines=lines, totals=totals, code=code, warning=warning,
                           quote_id=quote_id(lines, totals), revision=saved.get('revision', ''))


@bp.post('/cart/discount')
@login_required
def discount():
    saved = read_cart()
    revision = saved.get('revision')
    if not revision or not saved['items']:
        return redirect(url_for('shopping.cart'))
    code = '' if request.args.get('clear') == '1' else request.form.get('code', '').strip().upper()
    try:
        if len(code) > 24:
            raise ValueError('Discount codes are at most 24 characters.')
        quote([], code)
        table('carts').update_item(Key={'user_id': g.user['user_id']},
            UpdateExpression='SET discount_code = :code, revision = :next',
            ConditionExpression='revision = :old',
            ExpressionAttributeValues={':code': code, ':next': uuid.uuid4().hex, ':old': revision})
    except ValueError as error:
        flash(str(error))
    except ClientError as error:
        if error.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise
        flash('Your cart changed. Please try again.')
    return redirect(url_for('shopping.cart'))


@bp.post('/cart/update')
@login_required
def update():
    pid = request.form.get('product_id', '')
    try:
        qty = int(request.form.get('quantity', ''))
    except ValueError:
        abort(400, description='Quantity must be a whole number.')
    if not 0 <= qty <= 99:
        abort(400, description='Quantity must be between 0 and 99.')
    saved = read_cart()
    old_revision = saved.get('revision')
    if qty:
        product = table('products').get_item(Key={'product_id': pid or '-'}, ConsistentRead=True).get('Item')
        if not product or qty > product['stock']:
            flash('That quantity is unavailable.')
            return redirect(url_for('shopping.cart'))
        if pid not in saved['items'] and len(saved['items']) >= 20:
            abort(400, description='A cart may contain at most 20 different products.')
        saved['items'][pid] = qty
    else:
        saved['items'].pop(pid, None)
    saved['revision'] = uuid.uuid4().hex
    kwargs = {'ConditionExpression': 'attribute_not_exists(user_id)'}
    if old_revision:
        kwargs = {'ConditionExpression': 'revision = :r', 'ExpressionAttributeValues': {':r': old_revision}}
    try:
        table('carts').put_item(Item=saved, **kwargs)
    except ClientError as exc:
        if exc.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise
        flash('Your cart changed in another tab. Review it and try again.')
    return redirect(url_for('shopping.cart'))


@bp.post('/checkout')
@login_required
def checkout():
    revision = request.form.get('revision', '')
    if not revision or len(revision) != 32:
        abort(400, description='Review your cart before checkout.')
    key = {'user_id': g.user['user_id'], 'order_id': revision}
    if table('orders').get_item(Key=key, ConsistentRead=True).get('Item'):
        return redirect(url_for('shopping.order', order_id=revision))
    saved = read_cart()
    if saved.get('revision') != revision or not saved['items']:
        flash('Your cart changed or is empty. Review it before checkout.')
        return redirect(url_for('shopping.cart'))
    try:
        lines = cart_lines(saved)
        if any(p['quantity'] > p['stock'] for p in lines):
            raise ValueError('Stock changed. Update your cart before checkout.')
        totals = quote(lines, saved.get('discount_code', ''))
        if request.form.get('quote_id') != quote_id(lines, totals):
            raise ValueError('Your checkout summary changed. Review the updated total and try again.')
    except ValueError as exc:
        flash(str(exc))
        return redirect(url_for('shopping.cart'))
    order = dict(key, items=lines, **totals, customer_email=g.user['email'], fulfillment='placed',
                 status='SIMULATED — no payment collected', created_at=datetime.now(timezone.utc).isoformat())
    writes = [
        {'Put': {'TableName': table('orders').name, 'Item': order,
                 'ConditionExpression': 'attribute_not_exists(order_id)'}},
        {'Delete': {'TableName': table('carts').name, 'Key': {'user_id': g.user['user_id']},
                    'ConditionExpression': 'revision = :r', 'ExpressionAttributeValues': {':r': revision}}}]
    for line in lines:
        writes.append({'Update': {'TableName': table('products').name,
            'Key': {'product_id': line['product_id']}, 'UpdateExpression': 'SET stock = stock - :q ADD #ver :one',
            'ConditionExpression': 'stock >= :q AND (attribute_not_exists(#ver) OR #ver = :v)',
            'ExpressionAttributeNames': {'#ver': 'version'},
            'ExpressionAttributeValues': {':q': line['quantity'], ':v': line['version'], ':one': 1}}})
    if totals['discount_code']:
        writes.append({'ConditionCheck': {'TableName': table('discounts').name,
            'Key': {'code': totals['discount_code']}, 'ConditionExpression': '#pct = :pct',
            'ExpressionAttributeNames': {'#pct': 'percent'},
            'ExpressionAttributeValues': {':pct': totals['discount_percent']}}})
    try:
        current_app.extensions['db'].meta.client.transact_write_items(TransactItems=writes, ClientRequestToken=revision)
    except ClientError as exc:
        if exc.response['Error']['Code'] not in ('TransactionCanceledException', 'TransactionConflictException', 'IdempotentParameterMismatchException'):
            raise
        if table('orders').get_item(Key=key, ConsistentRead=True).get('Item'):
            return redirect(url_for('shopping.order', order_id=revision))
        flash('Stock, price, or cart changed. Review your cart and retry.')
        return redirect(url_for('shopping.cart'))
    return redirect(url_for('shopping.order', order_id=revision))


@bp.get('/orders')
@login_required
def orders():
    results, kwargs = [], {'KeyConditionExpression': Key('user_id').eq(g.user['user_id'])}
    while True:
        page = table('orders').query(**kwargs)
        results.extend(page['Items'])
        if 'LastEvaluatedKey' not in page:
            break
        kwargs['ExclusiveStartKey'] = page['LastEvaluatedKey']
    return render_template('orders.html', orders=sorted(results, key=lambda p: p['created_at'], reverse=True))


@bp.get('/orders/<order_id>')
@login_required
def order(order_id):
    saved = table('orders').get_item(Key={'user_id': g.user['user_id'], 'order_id': order_id}, ConsistentRead=True).get('Item')
    if not saved:
        abort(404)
    return render_template('order.html', order=saved)
