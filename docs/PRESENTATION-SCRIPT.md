# Campus Cart — 15-Minute Live Demonstration Script

## Preparation

Before presenting, have these ready:

- Flask and Docker Desktop running.
- Campus Cart open at
- An admin account signed in in the regular browser window.
- A private browser window for the customer demonstration.
- A fresh email address for registration.
- Several existing orders across different customers and totals.
- VS Code open to the project.
- Backup screenshots of the cart and order confirmation.

Use **Demo Lamp** as the new product created during the presentation. If it already exists from rehearsal, choose a distinct name so the audience can identify the new item.

Each group member can choose a section. The introduction speaker also delivers the closing. Rehearse finishing a little early to accommodate questions.

## 0:00–1:30 — Introduction and Architecture

**Action — Show the storefront.**

“Hello, everyone. We’re presenting Campus Cart, our database-driven online shopping application for CS 3773.

We’ll demonstrate the complete shopping workflow, beginning with account registration and ending with an order that an administrator can manage.

The application uses Python Flask for its routes and application logic, Jinja templates for generating pages, CSS for the interface, and boto3 for communicating with DynamoDB.

For this demonstration, DynamoDB Local runs through Docker Desktop on this computer.”

**Action — Briefly show the architecture diagram or README schema.**

“We use five tables. Users stores account information, Products stores the catalog, Carts stores customer selections, Orders stores completed purchases, and Discounts stores our coupon codes.

Keeping carts and orders in the database lets the application retain them between visits.

We’ll begin with the customer account features.”

**Handoff**

“Next, we’ll demonstrate registration and account management.”

## 1:30–3:30 — Registration, Login, and Account Editing

**Action — Switch to the private customer browser window and open Register.**

“I’ll create a new customer account.

Registration requires a name, an email address, and a password of at least twelve characters.”

**Action — Enter a demo name, a fresh email, and a prepared demo password. Click Register.**

“The application validates the submitted information and prevents duplicate registration with the same normalized email address.

Passwords are stored as secure hashes using Werkzeug. During login, the submitted password is checked against the stored hash.”

**Action — Log in.**

“After signing in, the navigation gives this customer access to their cart, orders, and account page.”

**Action — Open My account, change the name, and click Save name.**

“Customers can edit their own name here. The application identifies the account from the signed-in session.”

**Action — Point out the customer navigation.**

“Admin access is controlled separately. The application checks the user’s role on the server before allowing access to administrative routes.”

**Handoff**

“We’ll now show how customers find products.”

## 3:30–5:30 — Catalog, Search, and Sorting

**Action — Open Shop in the customer window.**

“The storefront displays each product’s image, name, description, price, and available quantity.

The quantity appears directly on the main shopping page, so customers can check availability while browsing.”

**Action — Search for `backpack`.**

“This search finds products using their name, description, or category.”

**Action — Clear the search. Select Price low to high and click Search.**

“Customers can sort by price to find products within their budget.”

**Action — Select Price high to low and click Search.**

“The reverse price sort is available as well.”

**Action — Select Availability most in stock and click Search.**

“This view sorts products by available quantity. The counts on the cards let us verify the order.”

**Action — Briefly resize the browser, then restore it.**

“The layout adjusts the number of product columns as the available screen width changes.”

**Handoff**

“Next, we’ll add a product and configure a promotion. We’ll purchase that same product during checkout.”

## 5:30–8:30 — Admin Product Management, Sales, and Discounts

**Action — Switch to the admin browser window and click Admin.**

“The administration page provides tools for managing products, sale prices, discount codes, users, and orders.

I’ll add a product so we can demonstrate how an administrative change reaches the customer storefront.”

**Action — Expand Add a product and enter the following.**

| Field | Value |
|---|---|
| Name | Demo Lamp |
| Category | Workspace |
| Description | A compact lamp for studying and desk work. |
| Regular price in cents | 2000 |
| Sale price in cents | 0 |
| Available quantity | 5 |

**Action — Save the product.**

“Prices are entered in integer cents. A value of two thousand represents twenty dollars.

Products can use an HTTPS image URL. When that field is blank, the application displays its fallback illustration.”

**Action — Expand the saved Demo Lamp. Change sale price to `1600` and save.**

“I’ll now put the lamp on sale for sixteen dollars while preserving the regular twenty-dollar price.”

**Action — Go to Discount codes. Create `STUDY10` with a percentage of `10`.**

“This code gives a further ten percent discount when a customer applies it to their cart.”

**Action — Open Users, expand the demonstration customer, edit their name, and save.**

“Administrators can also update a customer’s name through this page.”

**Action — Return to the customer window, refresh Shop, and search for Demo Lamp.**

“The new product is visible. Its card shows the regular price, the sale price, and five available units.”

**Handoff**

“We’ll now use this product to demonstrate cart management, discounts, tax, and checkout.”

## 8:30–11:30 — Cart, Pricing, and Checkout

**Action — In the customer window, set Demo Lamp quantity to `1` and click Set in cart.**

“The customer can choose a quantity and add the selection to their cart.”

**Action — In Cart, change quantity to `2` and click Update.**

“Updating the quantity recalculates the item subtotal.”

**Action — Change quantity to `0` and click Update.**

“A quantity of zero removes the item.”

**Action — Return to Shop and add one Demo Lamp again. Open Cart.**

“For our pricing example, we’ll purchase one lamp.”

**Action — Enter `STUDY10` and click Apply code.**

“The regular price is twenty dollars, and the sale price is sixteen dollars. The ten percent coupon saves another dollar and sixty cents.

That leaves fourteen dollars and forty cents before tax.

The assignment specifies an eight-point-two-five percent tax rate. Tax rounds to one dollar and nineteen cents, giving us a final total of fifteen dollars and fifty-nine cents.”

**Action — Point to each amount in the summary.**

| Summary line | Expected amount |
|---|---:|
| Subtotal | $16.00 |
| Coupon savings | −$1.60 |
| Tax | $1.19 |
| Total | **$15.59** |

“The server calculates these amounts from the stored product and discount records.”

**Action — Click Place simulated order.**

“Checkout saves the order, decreases inventory, and clears the matching cart using a DynamoDB transaction.

Those changes succeed together. If a required condition fails, such as insufficient stock, the transaction prevents a partial purchase.”

**Action — Show the confirmation, then Orders and the empty Cart.**

“The confirmation and order history preserve the purchase details and final total.

Checkout is simulated. This demonstration records the order and inventory changes.”

**Handoff**

“Next, we’ll show how administrators manage the saved order and explain our verification process.”

## 11:30–14:15 — Order Management, Testing, and Documentation

**Action — Switch to the admin window, refresh Admin, and go to Orders.**

“The customer’s purchase appears under Current orders.”

**Action — Expand the new order.**

“Here we can review its customer, timestamp, total, and purchased items.”

**Action — Demonstrate each order sort, clicking Sort after each selection.**

“The administrator can sort orders by newest date, customer email, or highest dollar total.”

**Action — Click Mark completed on the demonstration order.**

“Marking an order completed moves it into Order history, where its details remain available.”

**Action — Show Demo Lamp on the storefront.**

“The available stock has decreased from five units to four.”

**Action — Switch to a second terminal in VS Code and run the tests.**

```powershell
.\.venv\Scripts\python -m pytest -q
```

“Our automated suite contains ten tests. It uses Moto to emulate DynamoDB and exercises the Flask routes and database operations.

The tests cover account behavior, cart validation, customer order ownership, transaction rollback, repeat checkout, and the admin sale-and-discount workflow.”

**Action — Read the actual test result when it appears.**

“We also check the application manually against the running Docker database, as we’ve demonstrated today.”

**Action — Briefly show the README and project documentation.**

“The documentation explains how another teammate can install the dependencies, configure the local database, seed products, run tests, and start the website.

During integration, we resolved a Docker storage-permissions issue and a layout issue where product illustrations overflowed their cards. We checked the fixes by rerunning database setup and reviewing the corrected storefront.”

**Handoff**

“That completes the customer and administrator workflow. We’ll finish with a brief closing.”

## 14:15–15:00 — Closing

**Action — Return to the storefront or order confirmation.**

“Today we demonstrated account registration and editing, product search and sorting, administrative product management, sale prices, discount codes, tax calculation, checkout, and order history.

The same product moved through the complete workflow, from an administrator creating it to a customer purchasing it and an administrator completing the order.

Our development process included AI-assisted starter code, team review, integration fixes, automated tests, and manual verification. Our report documents that process and our contributions.

Thank you. We’re ready for your questions.”

## Short Answers for Questions

### Why did you choose Flask?

“Flask gave us a manageable Python application structure with routes, templates, and reusable modules for the required features.”

### What does Docker do?

“Docker runs DynamoDB Local. Flask runs in our Python environment and connects to the database through boto3.”

### What happens if two customers try to buy the last item?

“Checkout includes a stock condition inside the database transaction. A purchase that cannot satisfy that condition fails without partially saving the order.”

### How do you keep customers out of Admin?

“Each protected admin route checks the signed-in user’s role from the database.”

### Can customers see another customer’s order?

“The order lookup includes the authenticated customer’s ID. The test suite verifies that another customer receives a 404 response.”

### What happens if the checkout button is submitted twice?

“The cart revision identifies the order. Repeating a successful checkout returns the existing order.”

### How does the application calculate tax?

“We use the sale price, subtract the coupon discount, and calculate 8.25% tax on the remaining subtotal. Monetary calculations round to integer cents.”

### Is it hosted on AWS?

“Our current demonstration uses Flask and DynamoDB Local on this computer.”

If the group completes and verifies AWS hosting before presenting, replace that answer with the actual deployed architecture.

### How did you use AI?

“We used AI assistance to create and refine the starter implementation. The team reviewed the behavior, performed integration work, and verified the application through automated tests and live demonstrations.”

Each member should describe their own contribution accurately if asked for further detail.

## If Something Goes Wrong During the Demo

- **The site will not load.** Check that Flask is running and Docker Desktop shows the database container running.
- **A form has expired.** Reload the page and submit it again.
- **A product or coupon is missing.** Confirm both browser windows are connected to the same running site.
- **Stock is too low.** Update it through Admin, then review the customer’s cart again.
- **Checkout reports a changed summary.** Review the updated cart total and submit again.
- **A technical issue takes too long.** Show the prepared screenshots and explain the expected workflow accurately.

Keep passwords, secret values, and private configuration files off the presentation screen.
