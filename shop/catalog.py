"""Robert: product browse, search and sort."""
from flask import Blueprint, render_template, request
from .db import all_items, table
from .pricing import unit_price

bp = Blueprint('catalog', __name__)


@bp.get('/')
def index():
    q = request.args.get('q', '').strip()[:100]
    sort = request.args.get('sort', 'name')
    products = [p for p in all_items(table('products'))
                if q.lower() in (p['name'] + ' ' + p['category'] + ' ' + p['description']).lower()]
    keys = {'name': lambda p: p['name'].lower(), 'price_asc': lambda p: (unit_price(p), p['name']),
            'price_desc': lambda p: (-unit_price(p), p['name']),
            'availability': lambda p: (-p['stock'], p['name'])}
    products.sort(key=keys.get(sort, keys['name']))
    return render_template('catalog.html', products=products, q=q, sort=sort)
