"""Calculate simulated checkout totals in integer cents."""
from decimal import Decimal, ROUND_HALF_UP

from .db import table


def unit_price(product):
    return product.get('sale_cents') or product['price_cents']


def rounded(cents):
    return int(Decimal(cents).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def quote(lines, code):
    coupon = table('discounts').get_item(Key={'code': code}, ConsistentRead=True).get('Item') if code else None
    if code and not coupon:
        raise ValueError('Discount code was not found. Remove it or try a different code.')
    subtotal = sum(line['subtotal'] for line in lines)
    percent = int(coupon['percent']) if coupon else 0
    savings = rounded(Decimal(subtotal) * percent / 100)
    tax = rounded(Decimal(subtotal - savings) * Decimal('0.0825'))
    return dict(subtotal_cents=subtotal, discount_code=code, discount_percent=percent,
                discount_cents=savings, tax_cents=tax, total_cents=subtotal - savings + tax)
