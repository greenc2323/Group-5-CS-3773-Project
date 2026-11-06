import re

from werkzeug.security import check_password_hash
from shop.db import table, all_items
from conftest import post, sign_in


def revision(client):
    client.get('/cart')
    with client.application.app_context():
        with client.session_transaction() as s:
            user = table('users').get_item(Key={'email': s['email']})['Item']
        return table('carts').get_item(Key={'user_id': user['user_id']})['Item']['revision']


def checkout(client, rev):
    page = client.get('/cart').data
    match = re.search(rb'name="quote_id" value="([a-f0-9]+)"', page)
    return post(client, '/checkout', revision=rev, quote_id=match[1].decode() if match else '')


def test_accounts(app, client):
    assert b'12' in post(client, '/register', name='X', email='bad', password='short').data
    post(client, '/register', name='Student', email='STUDENT@example.com', password='safe-password-123')
    with app.app_context():
        user = table('users').get_item(Key={'email': 'student@example.com'})['Item']
        assert user['password_hash'] != 'safe-password-123'
        assert check_password_hash(user['password_hash'], 'safe-password-123')
    assert b'Unable to register' in post(client, '/register', name='Other', email='student@example.com', password='different-password').data
    assert b'incorrect' in post(client, '/login', email='student@example.com', password='wrong').data
    assert b'Log out' in post(client, '/login', email='student@example.com', password='safe-password-123').data
    post(client, '/logout')
    assert client.get('/cart').status_code == 302


def test_search_sort_and_no_match(client):
    assert b'Everyday Backpack' in client.get('/?q=backpack').data
    assert b'Desk Headphones' not in client.get('/?q=backpack').data
    assert b'No products found' in client.get('/?q=doesnotexist').data
    html = client.get('/?sort=price_asc').data
    assert html.index(b'Study Notebook') < html.index(b'Desk Headphones')
    html = client.get('/?sort=price_desc').data
    assert html.index(b'Desk Headphones') < html.index(b'Study Notebook')


def test_csrf_and_method_safety(client):
    assert client.post('/register', data={}).status_code == 400
    assert client.get('/logout').status_code == 405
    assert client.get('/checkout').status_code == 405
    sign_in(client)
    assert client.post('/cart/update', data={'csrf': 'wrong'}).status_code == 400


def test_cart_validation_and_removal(client):
    sign_in(client)
    assert post(client, '/cart/update', product_id='p001', quantity='abc').status_code == 400
    assert post(client, '/cart/update', product_id='p001', quantity='-1').status_code == 400
    assert b'unavailable' in post(client, '/cart/update', product_id='missing', quantity='1').data
    assert b'unavailable' in post(client, '/cart/update', product_id='p001', quantity='99').data
    post(client, '/cart/update', product_id='p001', quantity='2')
    assert b'$78.00' in client.get('/cart').data
    post(client, '/cart/update', product_id='p001', quantity='0')
    assert b'cart is empty' in client.get('/cart').data


def test_checkout_and_replay_and_isolation(app, client):
    sign_in(client)
    post(client, '/cart/update', product_id='p001', quantity='2')
    rev = revision(client)
    result = checkout(client, rev)
    assert b'ORDER CONFIRMED' in result.data
    assert b'$84.44' in result.data
    assert b'ORDER CONFIRMED' in checkout(client, rev).data
    assert b'cart is empty' in client.get('/cart').data
    with app.app_context():
        assert table('products').get_item(Key={'product_id': 'p001'})['Item']['stock'] == 13
        assert len(all_items(table('orders'))) == 1
    other = app.test_client()
    sign_in(other, 'other@example.com')
    assert other.get('/orders/' + rev).status_code == 404
    assert rev.encode() not in other.get('/orders').data


def test_stock_failure_is_atomic(app, client):
    sign_in(client)
    post(client, '/cart/update', product_id='p001', quantity='2')
    post(client, '/cart/update', product_id='p002', quantity='1')
    rev = revision(client)
    with app.app_context():
        table('products').update_item(Key={'product_id': 'p001'}, UpdateExpression='SET stock = :s', ExpressionAttributeValues={':s': 0})
    assert b'Stock changed' in checkout(client, rev).data
    with app.app_context():
        assert not all_items(table('orders'))
        assert table('products').get_item(Key={'product_id': 'p002'})['Item']['stock'] == 40
        assert all_items(table('carts'))[0]['items']['p001'] == 2


def test_stale_cart_and_seed_preserves_stock(app, client):
    sign_in(client)
    post(client, '/cart/update', product_id='p001', quantity='1')
    stale = revision(client)
    post(client, '/cart/update', product_id='p001', quantity='2')
    assert b'cart changed' in post(client, '/checkout', revision=stale).data
    rev = revision(client)
    checkout(client, rev)
    assert app.test_cli_runner().invoke(args=['init-db']).exit_code == 0
    assert app.test_cli_runner().invoke(args=['seed']).exit_code == 0
    with app.app_context():
        assert table('products').get_item(Key={'product_id': 'p001'})['Item']['stock'] == 13


def test_transaction_condition_rolls_back(app, client, monkeypatch):
    """Change stock after the pre-check, before DynamoDB's transaction."""
    sign_in(client)
    post(client, '/cart/update', product_id='p001', quantity='2')
    rev = revision(client)
    db_client = app.extensions['db'].meta.client
    real = db_client.transact_write_items
    def competing_purchase(**kwargs):
        with app.app_context():
            table('products').update_item(Key={'product_id': 'p001'}, UpdateExpression='SET stock = :s', ExpressionAttributeValues={':s': 0})
        return real(**kwargs)
    monkeypatch.setattr(db_client, 'transact_write_items', competing_purchase)
    assert b'Stock, price, or cart changed' in checkout(client, rev).data
    with app.app_context():
        assert all_items(table('orders')) == []
        assert all_items(table('carts'))[0]['items']['p001'] == 2


def test_html_is_escaped(client):
    post(client, '/register', name='<script>alert(1)</script>', email='escape@example.com', password='safe-password-123')
    data = post(client, '/login', email='escape@example.com', password='safe-password-123').data
    assert b'<script>alert(1)</script>' not in data
    assert b'&lt;script&gt;' in data


def test_admin_promotion_checkout_and_order_history(app, client):
    sign_in(client)
    assert client.get('/admin/').status_code == 403
    assert post(client, '/admin/discounts', code='STUDY10', percent='10').status_code == 403
    assert b'Updated Student' in post(client, '/account', name='Updated Student').data

    admin = app.test_client()
    sign_in(admin, 'staff@example.com')
    result = app.test_cli_runner().invoke(args=['grant-admin', 'staff@example.com'])
    assert result.exit_code == 0, result.output
    assert admin.get('/admin/').status_code == 200
    assert b'Demo Lamp' in post(admin, '/admin/products', name='Demo Lamp',
        category='Desk', description='A lamp for the demo.', price_cents='2000',
        sale_cents='1600', stock='80').data
    assert b'STUDY10' in post(admin, '/admin/discounts', code='STUDY10', percent='10').data
    with app.app_context():
        product = next(p for p in all_items(table('products')) if p['name'] == 'Demo Lamp')
    catalog = client.get('/?sort=availability').data
    assert catalog.index(b'Demo Lamp') < catalog.index(b'Study Notebook')
    assert b'products/default.svg' in catalog

    post(client, '/cart/update', product_id=product['product_id'], quantity='1')
    cart = post(client, '/cart/discount', code='study10')
    for expected in (b'$16.00', b'$1.60', b'$1.19', b'$15.59'):
        assert expected in cart.data
    rev = revision(client)
    assert b'$15.59' in checkout(client, rev).data
    with app.app_context():
        order = all_items(table('orders'))[0]
        assert order['total_cents'] == 1559
        assert order['tax_cents'] == 119
        assert order['discount_cents'] == 160
    assert rev.encode() in admin.get('/admin/?sort=customer').data
    post(admin, '/admin/orders/complete', user_id=order['user_id'], order_id=rev)
    assert rev.encode() in admin.get('/admin/?sort=total').data.split(b'Order history')[1]
