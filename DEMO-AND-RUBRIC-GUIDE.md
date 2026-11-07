Campus Cart — Rubric Demonstration and Questions Guide

Use this guide to rehearse the requirements in the project grading PDF. The instructor also references a separate demonstration checklist. Review that checklist before the final demonstration.

## Before the presentation

Choose one computer for the entire demonstration. Its local database contains the accounts, products, discount codes, and orders used during the demonstration.

Prepare the following items.

- An admin account in the regular browser window.
- A customer account in a private browser window.
- Several existing products with available stock.
- A completed order for demonstrating order history.
- VS Code open to the project.
- Docker Desktop running.
- Backup screenshots.
- The final report and architecture diagram.

Use demo passwords and remember which account belongs to each browser window.

### Start the application

Open the project folder in VS Code and open a PowerShell terminal.

```powershell
docker compose up -d
.\.venv\Scripts\python -m flask --app app run
```

Open the site in your browser.

```text
http://127.0.0.1:5000
```

For a fresh database, run these before starting Flask.

```powershell
.\.venv\Scripts\python -m flask --app app init-db
.\.venv\Scripts\python -m flask --app app seed
```

### Enable your admin account

Register the account through the website first. Open a second project terminal and run the following, using the registered email.

```powershell
.\.venv\Scripts\python -m flask --app app grant-admin "staff@example.com"
```

Sign in with that account and refresh the page. Confirm the Admin link appears.

## 1. Intuitive UI/UX

**Possible request**

“Show us how a customer uses your website.”

**Demonstration**

1. Open Shop.
2. Point out the search field, sorting choices, product images, prices, and stock counts.
3. Show the navigation links for Cart, Orders, and My account.
4. Resize the browser to demonstrate how the product cards adapt.
5. Search for something that produces no matches and show the empty result message.

**Explanation**

“The interface groups the main shopping actions together. Customers can find products, review availability, manage their selections, and see their saved orders.”

Mobile friendliness is listed as a bonus. Check the narrow layout before presenting it.

## 2. Web application and database

**Possible requests**

“What technologies did you use?”

“Where is the information stored?”

**Demonstration**

1. Open the running website.
2. Show that Flask is running in the terminal.
3. Open Docker Desktop and show the DynamoDB container.
4. Show the database schema in the README or architecture diagram.

**Explanation**

“Flask receives requests and runs the application logic. Jinja generates the HTML pages, and CSS styles them. Boto3 connects the application to DynamoDB Local, which runs through Docker.”

| Table | Records |
|---|---|
| Users | Names, login emails, password hashes, and roles |
| Products | Descriptions, images, prices, sale prices, and stock |
| Carts | Each customer's selected products and quantities |
| Orders | Saved purchases, totals, timestamps, and completion state |
| Discounts | Discount codes and percentage savings |

**Possible question**

“Is the site hosted in the cloud?”

**Answer**

“Our current demonstration runs locally. Flask and DynamoDB Local are running on this computer.”

The rubric lists cloud hosting as extra credit.

## 3. Register an account

**Possible request**

“Create a new customer account.”

**Demonstration**

1. Use the private browser window.
2. Click Register.
3. Enter a demo name and a unique email address.
4. Enter a password of at least 12 characters.
5. Click Register.
6. Sign in with that email and password.

**Expected result**

The account is created, and the signed-in navigation appears.

**Possible question**

“What happens if the email already exists?”

**Answer**

“The application normalizes emails to lowercase and uses a conditional database write to prevent duplicate registration.”

Demonstrate duplicate registration using an existing demo email.

## 4. Modify customer information

**Possible request**

“Can the customer change their information?”

**Demonstration**

1. Sign in as the customer.
2. Click My account.
3. Change the name.
4. Click Save name.
5. Confirm the new name appears.

**Explanation**

“The customer updates their name on their own account. The server identifies the account from the signed-in session.”

The current account editor changes the name. Explain that scope accurately if asked about changing emails or passwords.

## 5. Product images, prices, and quantities

**Possible request**

“Show the information available before opening a product.”

**Demonstration**

1. Open Shop.
2. Point to a product's image.
3. Point to its displayed price.
4. Point to its available quantity on the main page.

**Explanation**

“The main product cards show the image, description, price, and available quantity.”

The included products use bundled SVG illustrations. Admins can enter an HTTPS image URL for a custom product.

## 6. Add a product

**Possible request**

“Add a new item for sale.”

**Demonstration**

1. In the admin window, click Admin.
2. Under Products and sale prices, expand Add a product.
3. Enter the following values.

| Field | Value |
|---|---|
| Name | Demo Lamp |
| Category | Workspace |
| Description | A compact lamp for the presentation demo. |
| Regular price in cents | 2000 |
| Sale price in cents | 0 |
| Available quantity | 5 |
| HTTPS image URL | Use a prepared image URL or leave blank for the fallback illustration |

4. Click Save product.
5. Open Shop and search for Demo Lamp.

**Expected result**

Demo Lamp appears for **$20.00** with **5 available**.

**Possible question**

“Why enter prices in cents?”

**Answer**

“Using integer cents keeps stored monetary values exact. Two thousand cents represents twenty dollars.”

## 7. Modify an item and create a sale

**Possible request**

“Change an existing item.”

**Demonstration**

1. Return to Admin.
2. Expand Demo Lamp.
3. Change its description to demonstrate a text edit.
4. Keep the regular price at 2000.
5. Set the sale price to 1600.
6. Save the product.
7. Return to Shop and search for Demo Lamp.

**Expected result**

The card shows the Sale label, the crossed-out regular price of **$20.00**, the sale price of **$16.00**, and available stock.

**Explanation**

“The sale price becomes the price used in the cart. The regular price stays visible so customers can identify the sale.”

## 8. Search and sort products

**Possible request**

“Search by item or description.”

**Demonstration**

1. Search for Demo Lamp.
2. Search for a word from a product description.
3. Clear the search to restore the full catalog.

**Possible request**

“Sort by price.”

**Demonstration**

1. Select Price low to high.
2. Click Search.
3. Confirm the lowest-priced products appear first.
4. Repeat using Price high to low.

**Possible request**

“Sort by availability.”

**Demonstration**

1. Select Availability most in stock.
2. Click Search.
3. Compare the stock counts of the first few products.

**Explanation**

“For this small catalog, the application reads the catalog and filters and sorts it in Python. A larger store would need a more scalable search design.”

## 9. Create and modify the shopping cart

**Possible request**

“Add an item, change its quantity, and remove it.”

**Demonstration**

1. In the customer window, find Demo Lamp.
2. Set the quantity to 1.
3. Click Set in cart.
4. Open Cart.
5. Change the quantity to 2 and click Update.
6. Confirm the item subtotal changes.
7. Set the quantity to 0 and click Update to remove it.
8. Add one Demo Lamp again for the checkout demonstration.

**Explanation**

“Setting a quantity replaces the existing cart quantity. Zero removes the product.”

**Possible question**

“Does adding an item reserve the stock?”

**Answer**

“Stock is checked when the cart is updated and again during checkout. The purchase reduces stock when checkout succeeds.”

## 10. Create and apply a discount code

**Possible request**

“Create a discount and show its effect in the cart.”

**Demonstration**

1. In the admin window, open Admin.
2. Under Discount codes, enter STUDY10.
3. Enter 10 for the percentage.
4. Click Save discount code.
5. In the customer window, open Cart.
6. Enter STUDY10 in Discount code.
7. Click Apply code.

**Expected result**

The cart displays the code, percentage, and dollar savings.

**Explanation**

“The app supports one percentage discount code per cart. It applies the code to the subtotal after sale prices are used.”

**Possible request**

“Try an invalid discount.”

Enter UNKNOWNCODE and click Apply code. The page should show a validation message. Reapply STUDY10 before continuing.

## 11. Tax and order summary

**Possible request**

“Explain how you calculate the final price.”

Use one Demo Lamp with a $16.00 sale price and STUDY10.

| Calculation | Amount |
|---|---:|
| Subtotal using the sale price | $16.00 |
| 10% coupon savings | −$1.60 |
| Amount after coupon | $14.40 |
| Tax at 8.25% | $1.19 |
| Final total | **$15.59** |

**Explanation**

“We apply the sale price first, subtract the coupon discount, and then calculate 8.25% tax on the discounted subtotal. Discount and tax amounts round to cents, with half cents rounded up.”

Show the subtotal, discount, tax, and total on the screen while explaining them.

## 12. Place an order

**Possible request**

“Complete the purchase.”

**Demonstration**

1. Review the cart summary.
2. Click Place simulated order.
3. Show the order confirmation.
4. Confirm the total is $15.59.
5. Open Orders and show the saved order.
6. Open Cart and show that it is empty.
7. Return to Shop and confirm Demo Lamp stock decreased from 5 to 4.

**Explanation**

“Checkout saves the order, reduces stock, and clears the matching cart in one DynamoDB transaction.”

**Possible question**

“Are payments processed?”

**Answer**

“Checkout is simulated. The order records the purchase details and updates stock.”

## 13. Modify users through Admin

**Possible request**

“Show how an administrator modifies a user.”

**Demonstration**

1. Open Admin.
2. Go to Users.
3. Expand the customer's email.
4. Edit the customer's name and save.
5. Refresh the customer window to show the change.

**Explanation**

“Admin access is checked on the server. Regular registration creates a customer account. Admin access is granted through a terminal command.”

The current admin user editor changes names.

## 14. Current orders and order history

**Possible request**

“Show the order that was just placed.”

**Demonstration**

1. In Admin, go to Orders.
2. Locate the purchase under Current orders.
3. Expand it to show the order ID and items.
4. Click Mark completed.
5. Find it under Order history.

**Explanation**

“New orders have a placed fulfillment state. Marking one completed moves it into the history section.”

## 15. Sort orders

**Possible request**

“Sort the orders by date, customer, and dollar amount.”

Use the Sort orders field and click Sort after each selection.

| Selection | Behavior |
|---|---|
| Newest first | Sorts by order timestamp, newest first |
| Customer email | Sorts alphabetically by customer email |
| Highest total | Sorts by dollar total, highest first |

Prepare at least three orders across two customers with different totals. This makes the sort changes visible.

## 16. Security and failure questions

### How are passwords stored?

“Werkzeug generates secure password hashes. Login checks the submitted password against the stored hash.”

If asked to show the code, open `shop/auth.py`. Avoid displaying passwords or private settings.

### Can a customer open the Admin page?

In the customer window, type:

```text
http://127.0.0.1:5000/admin/
```

The expected response is **403 Forbidden**.

“The route checks the signed-in user's database role before allowing access.”

### Can a customer see another customer's order?

“Order retrieval uses both the signed-in customer's ID and the requested order ID.”

Copy an order URL from one customer into a browser signed in as a different customer. The expected response is **404**.

### What happens if stock is insufficient?

Prepare a separate low-stock product. Attempt to set a cart quantity higher than its stock.

The app should reject the quantity and show a message.

“For a stock change during checkout, the transaction condition prevents an order from partially changing the database.”

### What if a price changes while the customer is checking out?

“The application recalculates the checkout summary on the server. If it differs from the displayed summary, the customer must review the updated total before trying again.”

### What if checkout is submitted twice?

“The order ID comes from the cart revision. A repeated successful checkout returns the existing order.”

### Why use a transaction?

“The order, stock changes, and cart removal must succeed together. A failure should preserve a consistent database state.”

## 17. Automated tests

**Possible request**

“Show how you tested the project.”

Open a separate terminal in the project folder.

```powershell
.\.venv\Scripts\python -m pytest -q
```

The current suite contains **10 tests**. Show the result from the actual run.

**Explanation**

“The tests use Moto to emulate DynamoDB. They exercise authentication, validation, carts, order ownership, transaction failures, and the admin sale-and-discount workflow.”

Explain that emulator tests and live Docker checks serve different purposes. The live demo verifies the locally running application and database connection.

## 18. Agile, Scrum, and team contributions

**Possible questions**

- How did you divide the work?
- Who acted as Scrum Master and Product Owner?
- How did you track tasks and integration problems?
- What did each person contribute?
- How did you review changes?
- How did you use AI?

Team responsibilities should match the work members actually perform. Update the report if responsibilities change.

For development problems, explain the Docker storage-permissions issue and the overflowing product illustrations. Describe the symptom, the fix, and how the result was checked.

Explain AI assistance accurately and describe how the team reviewed and verified the implementation.

## 19. Final report and peer review

The grading PDF calls for one report of approximately 10 pages, submitted by one member.

Prepare the report using the instructor's report template. Include the required workflow artifacts, diagrams, design justifications, development process, and documented deviations.

| Category | Weight |
|---|---:|
| Functionality | 30% |
| UI/UX | 20% |
| Demonstration | 15% |
| Final report | 10% |
| Peer review | 25% |

Each member must participate and submit the required confidential peer review of teammates.

## Final rehearsal checklist

- [ ] All six members can attend.
- [ ] The live demonstration fits within 15 minutes.
- [ ] Each member knows their browser actions and explanation.
- [ ] Customer registration and name editing work.
- [ ] Products show images, prices, and quantities on the main page.
- [ ] Adding and editing products works.
- [ ] Description search and all required sorts work.
- [ ] Cart quantity updates and removal work.
- [ ] Sale prices and coupon savings appear in the cart.
- [ ] The 8.25% tax and final total are correct.
- [ ] Checkout saves the order and decreases stock.
- [ ] Admin user-name editing works.
- [ ] Current orders and completed history work.
- [ ] Orders can be sorted by date, customer, and total.
- [ ] Automated tests pass in the demonstration environment.
- [ ] The final report is ready.
- [ ] The instructor's separate demonstration checklist has been reviewed.
