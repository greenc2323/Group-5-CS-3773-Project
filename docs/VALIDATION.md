# Validation record

Validated November 5, 2026 with Python 3.12 on Windows.

Command: `python -m pytest -q`

Result: **10 passed in 12.27s**.

Tests execute real Flask routes, Werkzeug password hashing, boto3 table operations and DynamoDB transactions against Moto's in-process emulator. No live AWS account was used, and no real payments were implemented or submitted. AWS IAM, Docker DynamoDB Local and a hosted HTTPS deployment were not exercised in this validation.

The suite covers account registration/login/logout, invalid inputs, duplicate accounts, CSRF and POST-only mutations, search and sorting, cart edits and removal, successful checkout, saved order totals, stock decrements, repeat checkout, order ownership, stale cart rejection, stock failures and transaction rollback, seed idempotence, and HTML escaping.

An initial test failure identified platform-dependent seed-file text decoding. The loader now explicitly reads UTF-8, and fixture setup checks for seed errors.

The admin workflow test covers access control, account editing, product creation, availability sorting, a sale and coupon, 8.25% tax, and moving a saved order into history.
