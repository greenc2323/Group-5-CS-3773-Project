import os
import secrets
from datetime import timedelta
from decimal import Decimal
import click
from dotenv import load_dotenv
from flask import Flask, abort, g, render_template, request, session
from botocore.exceptions import BotoCoreError, ClientError
from .db import resource, setup, table


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=os.getenv('SECRET_KEY'),
        AWS_DEFAULT_REGION=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        DYNAMODB_ENDPOINT_URL=os.getenv('DYNAMODB_ENDPOINT_URL'),
        TABLE_PREFIX=os.getenv('TABLE_PREFIX', 'cs3773-dev'),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2), MAX_CONTENT_LENGTH=16384)
    if test_config:
        app.config.update(test_config)
    if not app.secret_key or len(app.secret_key) < 32 or app.secret_key.startswith('replace-with-'):
        raise RuntimeError('Set SECRET_KEY to a random value of at least 32 characters. See README.')
    app.extensions['db'] = resource(app.config)

    @app.before_request
    def protect():
        if request.method == 'POST':
            expected = session.get('csrf')
            supplied = request.form.get('csrf', '')
            if not expected or not secrets.compare_digest(expected, supplied):
                abort(400, description='Invalid or expired form. Reload the page and try again.')
        g.user = None
        if session.get('email'):
            g.user = table('users').get_item(Key={'email': session['email']}, ConsistentRead=True).get('Item')

    @app.context_processor
    def helpers():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_hex(32)
        return {'csrf': session['csrf']}

    app.jinja_env.filters['money'] = lambda cents: f'${Decimal(cents) / 100:,.2f}'
    from .auth import bp as auth
    from .catalog import bp as catalog
    from .shopping import bp as shopping
    from .admin import bp as admin
    for bp in (auth, catalog, shopping, admin):
        app.register_blueprint(bp)

    @app.errorhandler(ClientError)
    @app.errorhandler(BotoCoreError)
    def database_error(error):
        app.logger.exception('DynamoDB request failed')
        return render_template('error.html', message='Database unavailable. Check your AWS configuration and table setup.'), 503

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def request_error(error):
        return render_template('error.html', message=error.description), error.code

    @app.cli.command('init-db')
    def init_db():
        """Create any missing tables, without deleting existing data."""
        setup(app.extensions['db'], app.config['TABLE_PREFIX'])
        click.echo('Tables ready.')

    @app.cli.command('grant-admin')
    @click.argument('email')
    def grant_admin(email):
        """Grant admin access to an existing account."""
        try:
            table('users').update_item(Key={'email': email.strip().lower()},
                UpdateExpression='SET #role = :admin', ConditionExpression='attribute_exists(email)',
                ExpressionAttributeNames={'#role': 'role'}, ExpressionAttributeValues={':admin': 'admin'})
        except ClientError as error:
            if error.response['Error']['Code'] != 'ConditionalCheckFailedException':
                raise
            raise click.ClickException('Register this account first.') from error
        click.echo('Admin access granted.')

    @app.cli.command('seed')
    def seed():
        """Insert missing sample products; never reset existing stock."""
        import json
        from pathlib import Path
        products = json.loads((Path(app.root_path).parent / 'data/products.json').read_text(encoding='utf-8'))
        for product in products:
            try:
                table('products').put_item(Item=product, ConditionExpression='attribute_not_exists(product_id)')
            except ClientError as exc:
                if exc.response['Error']['Code'] != 'ConditionalCheckFailedException':
                    raise
        click.echo('Sample products ready.')
    return app
