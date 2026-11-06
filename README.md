# Campus Cart — CS 3773 starter MVP

A six-person course project using Flask and DynamoDB. Customers can edit their name, browse and sort products, apply discounts and place simulated orders. Staff can manage products, sale prices, discount codes, customer names and order history.

## Upgrade an existing local install

Stop Flask with Ctrl+C. Extract the updated ZIP, then copy its project files over the existing project folder. Keep your existing `.env`, `.venv`, and Docker volume. Use the same folder, table prefix and database endpoint to keep your data. Start Docker Desktop and run `docker compose up -d` in that folder. Run `init-db` again to create the missing discounts table. Existing sample products automatically show the bundled product illustrations.

## Set up the admin demo

Register your staff account through the website. In a second PowerShell terminal in the project folder, run the following with the email you registered:

```powershell
.\.venv\Scripts\python -m flask --app app grant-admin "staff@example.com"
```

Refresh the page while signed in. The **Admin** link appears. Use a separate customer account for checkout. In Admin, add a product with a regular price of 2000 cents, a sale price of 1600 cents, and positive stock. Save a 10% code such as STUDY10. As the customer, add one unit, apply the code, and confirm a $1.60 discount, $1.19 tax, and $15.59 total. Place the simulated order, find it in **Current orders**, then mark it completed to move it to **Order history**.

Prices use integer cents. Checkout applies the sale price, then one percentage code, then 8.25% tax. The discount and tax each round to the nearest cent, with half cents rounded up. Custom products can use an HTTPS image URL and have a bundled fallback illustration. Completing an order records a demo status change.

## Quick start (VS Code on Windows)

Campus Cart uses **DynamoDB Local through Docker Desktop**. Install Python 3.11 or newer and start Docker Desktop. Extract the ZIP, open the extracted `online-shopping` folder in VS Code, and open a PowerShell terminal in that folder.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
.\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
notepad .env
```

Replace the `SECRET_KEY` placeholder with the generated value. Remove the leading `#` from these three lines, then save and close Notepad.

```dotenv
DYNAMODB_ENDPOINT_URL=http://localhost:8000
AWS_ACCESS_KEY_ID=local
AWS_SECRET_ACCESS_KEY=local
```

The `local` values are dummy credentials. Keep `.env` private. Once Docker Desktop shows **Engine running**, run these commands one at a time.

```powershell
docker compose up -d
.\.venv\Scripts\python -m flask --app app init-db
.\.venv\Scripts\python -m flask --app app seed
.\.venv\Scripts\python -m flask --app app run
```

Wait for **Tables ready.** and **Sample products ready.** before proceeding to the next command. Open [Campus Cart](http://127.0.0.1:5000), register an account with a password of 12–128 characters, and sign in.

Docker keeps each teammate's records in a local volume. On later runs, start Docker Desktop, run `docker compose up -d`, and start Flask again. Press Ctrl+C to stop Flask and run `docker compose stop` to stop the database. Re-running `init-db` preserves existing data. Re-running `seed` inserts missing sample products and preserves existing stock.

## Automated tests

```powershell
.\.venv\Scripts\python -m pytest -q
```

Tests use Moto's in-process DynamoDB emulator, temporary tables and dummy credentials. They do not contact an AWS account. Coverage includes authentication, hashing, duplicate email, validation, CSRF, logout, search/sorting, carts, order ownership, stock failure, atomic transaction rollback, stale carts, repeat checkout, output escaping, and safe re-seeding. GitHub Actions runs the suite on push and pull request. Run the checkout workflow against DynamoDB Local before the class demo.

## Data and behavior

The tables use on-demand capacity (`PAY_PER_REQUEST`). Their names combine `TABLE_PREFIX` with the suffixes below.

| Table | Partition key | Sort key | Purpose |
|---|---|---|---|
| users | email (normalized lowercase) | — | Unique login, UUID user_id, name, scrypt password hash, customer role |
| products | product_id | — | Name, description, category, price_cents, stock, display symbol |
| carts | user_id | — | Product-to-quantity map and revision UUID |
| orders | user_id | order_id | Timestamp, price/name snapshots, total_cents, simulated status |
| discounts | code | — | Percentage off applied to the cart subtotal |

Cart quantities replace the previous quantity. Zero removes an item. Carts persist across sessions. Each cart can contain up to 20 different products and 99 units per product. Checkout updates stock and saves the priced order in one transaction.

Checkout re-reads product prices and stock on the server, then atomically writes the order, conditionally decreases stock, and deletes the matching cart revision in one DynamoDB transaction. A changed cart, insufficient stock, or a concurrent price update prevents the entire transaction. Customers should review the cart again after a conflict. An order ID is the cart revision; replaying a successful submission returns that same order instead of purchasing twice. Order access always includes the authenticated user's ID.

For a class-sized catalog, paginated DynamoDB scans feed application-side substring search and sorting. This loads the entire catalog and is intentionally unsuitable for a large store; add indexed access patterns/search infrastructure before scaling. Order history uses a partition-key query and pagination.

## Team ownership

The proposal names are preserved. See `docs/TEAM.md` for interfaces and acceptance criteria.

| Team member | Ownership |
|---|---|
| Cain Green — Scrum Master / repository owner | DynamoDB Local setup, `shop/db.py`, schema and integration coordination |
| Robert Rodriguez — Product Owner | `shop/catalog.py`, templates/CSS, cart/checkout user flow and scope decisions |
| Mathew Davis — Developer | `tests/`, test evidence, optional restock notification design |
| Mathew Belcher — Developer | README, `docs/`, deployment instructions and demo checklist |
| Alex Vasquez — Developer | shop/auth.py, password policy, authentication and session integration |
| Teya Machani — Team member | Responsibility to be confirmed by the team |

`shop/shopping.py` is a shared integration module: Robert owns the user flow, Cain reviews transactions, Alex reviews ownership checks, Mathew Davis validates failures, and Mathew Belcher documents it. Each change should have one branch, an issue with acceptance criteria, and one teammate's review before merging.

## Security and deployment boundary

Passwords use Werkzeug scrypt hashes. Flask signs session cookies; only the normalized login email and CSRF token are stored there (no passwords, cart, or AWS credentials). Cookies are HTTP-only, SameSite=Lax, with a two-hour session lifetime. All state changes require POST and a session CSRF token; Jinja escapes text. A strong stable `SECRET_KEY` is required at startup; changing it signs everyone out. Logout is POST-only and clears the current browser session.

For a class demo beyond localhost, use HTTPS, set `COOKIE_SECURE=true`, keep debug mode off, configure protected credentials/roles, and run a production WSGI server, for example:

```powershell
.\.venv\Scripts\waitress-serve --listen=127.0.0.1:8080 app:app
```

Put an HTTPS reverse proxy in front of that local listener. The included Flask server is for local development. This starter does not implement email verification, password reset, login rate limiting, MFA, server-side session revocation, or production monitoring. Add those before use with real customer accounts. Public registration always creates a customer; no endpoint allows role changes. Avoid real personal data in your demonstration.

## Troubleshooting

- **SECRET_KEY startup error:** generate a random secret, replace the placeholder in `.env`, and run commands from the project directory.
- **ResourceNotFoundException:** region, endpoint and prefix must match the values used for `init-db`.
- **Connection refused at port 8000:** start Docker Desktop and `docker compose up -d`.
- **Expired form:** reload and submit again. Signing in rotates the session and invalidates older forms.
- **No stock after demos:** repeated orders intentionally reduce stock. Use a fresh table prefix for fresh seed data; no destructive reset script is supplied.
- **Port 5000 busy:** use `python -m flask --app app run --port 5001`.

## References

- Flask sessions and configuration: https://flask.palletsprojects.com/en/stable/quickstart/#sessions
- Boto3 transactions: https://docs.aws.amazon.com/boto3/latest/reference/services/dynamodb/client/transact_write_items.html
- Boto3 credentials: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
- DynamoDB Local: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html

This is an AI-assisted starter implementation. Record your team's changes, tests, integration attempts and AI usage in the final report. Use the separate demonstration checklist and report template for final submission.
