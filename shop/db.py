"""Cain: DynamoDB connection, table definitions, and paginated access."""
import boto3
from flask import current_app

KEYS = {'users': [('email', 'HASH')], 'products': [('product_id', 'HASH')], 'discounts': [('code', 'HASH')],
        'carts': [('user_id', 'HASH')], 'orders': [('user_id', 'HASH'), ('order_id', 'RANGE')]}


def resource(config):
    return boto3.resource('dynamodb', region_name=config['AWS_DEFAULT_REGION'],
                          endpoint_url=config.get('DYNAMODB_ENDPOINT_URL') or None)


def table(name):
    return current_app.extensions['db'].Table(current_app.config['TABLE_PREFIX'] + '-' + name)


def all_items(table_obj, **kwargs):
    items = []
    while True:
        page = table_obj.scan(**kwargs)
        items.extend(page.get('Items', []))
        if 'LastEvaluatedKey' not in page:
            return items
        kwargs['ExclusiveStartKey'] = page['LastEvaluatedKey']


def setup(db, prefix):
    for name, keys in KEYS.items():
        obj = db.Table(prefix + '-' + name)
        try:
            obj.load()
        except db.meta.client.exceptions.ResourceNotFoundException:
            obj = db.create_table(TableName=obj.name, BillingMode='PAY_PER_REQUEST',
                KeySchema=[{'AttributeName': k, 'KeyType': t} for k, t in keys],
                AttributeDefinitions=[{'AttributeName': k, 'AttributeType': 'S'} for k, _ in keys])
        obj.wait_until_exists()
