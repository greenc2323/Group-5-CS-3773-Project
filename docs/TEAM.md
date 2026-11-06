# Team integration guide

## Architecture

Browser → Flask request/CSRF/session checks → auth/catalog/shopping/admin blueprints → shared boto3 resource → five DynamoDB tables. Flask renders Jinja templates and a local CSS file. No JavaScript framework, separate API service, payment provider or email service is required.

## Contracts and ownership

| Owner | Module boundary | Acceptance criteria |
|---|---|---|
| Cain Green | `db.resource`, `db.table`, `db.setup`, table prefix and schema | Fresh environment initializes five tables; re-running setup preserves records; runtime role accesses only app tables. |
| Robert Rodriguez | Catalog GET `/`; templates and shopping routes | Search name/category/description, sort both price directions, responsive pages, clear demo checkout and usable empty states. |
| Alex V. | `/register`, `/login`, POST `/logout`, `login_required`, `g.user` | Unique normalized email, password hash only, session rotation, protected writes, no cross-user order access. |
| Mathew D. | Moto fixtures, workflow/failure tests | Suite runs without AWS; failed transactions create no order and preserve the cart. Optional restock alerts remain backlog. |
| Mathew B. | Setup, deployment and architecture documentation | Another member can unzip, start a database, seed, register and complete an order following only README. |

Product records use `product_id`, `name`, `description`, `category`, `price_cents`, `stock`, and `symbol`. Keep monetary values in cents. `g.user` is the authenticated database record; never accept a posted user ID or price. Cart writes replace the saved map under an optimistic revision condition. Checkout consumes that revision atomically. Change these contracts together with tests and documentation.

## Suggested next issues

1. Each teammate independently runs the quick start and records an integration result.
2. Cain verifies IAM and an AWS/DynamoDB Local demo with the agreed prefix and region.
3. Robert confirms required features and obtains instructor feedback on the storefront.
4. Alex and Mathew D. review authentication and transaction failures together.
5. Mathew B. gathers screenshots and completes a report using the actual instructor template.
6. Optional: define restock subscriptions and access controls before adding email. Do not put email sends inside checkout transactions; use an outbox/stream-based design if later required.

## Demo checklist

- Browse all six seeded products, search for a category, and sort by price.
- Register two different customers; demonstrate invalid login and logout.
- Set a cart quantity, change it, remove it, and demonstrate an empty cart.
- Checkout; show the simulated label, order total, reduced stock and empty cart.
- Show that a second customer cannot see the first customer's orders.
- Run the tests and record their actual output.

For report evidence, keep dates, feature owners, pull requests, integration failures/fixes, and AI-assisted work. Do not describe optional alerts or real payments as implemented.
