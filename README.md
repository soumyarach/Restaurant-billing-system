# Bharat Bhojan Restaurant Billing
Bharat Bhojan – Restaurant Billing System

This project is a Python-based restaurant billing application built with Tkinter (GUI) and SQLite (database).
It helps restaurant staff manage menu items, take orders, calculate bills, and generate sales reports.

🔑 Features

Login system (Admin/Cashier roles).

Dynamic Menu – loaded from menu.csv into SQLite database.

Order Management – add/remove items, set quantity, apply discounts.

Billing – auto calculation of subtotal, discount, GST, and final total.

Payment Methods – supports Cash & UPI (with generated payment link).

Dine-in Tables – allocate/free tables for dine-in customers.

Bill Output – display in GUI, save as .txt, and share via WhatsApp/Email.

Sales Report – export daily/monthly transactions to sales_report.csv.

Sample Bills – test data provided in sample_bill.json.

🛠️ Tech Stack

Python 3.x

Tkinter (GUI)

SQLite (Database)

Pillow (Image handling)

CSV/JSON (Data storage & testing)

📂 Project Structure
restaurant_billing/
│── app.py                # Entry point
│── db/restaurant.db      # SQLite database
│── data/menu.csv         # Menu items
│── data/sample_bill.json # Test bills
│── data/sales_report.csv # Saved sales
│── ui/main_ui.py         # GUI application
│── README.md             # Project info

🚀 How to Run

Install requirements:

pip install pillow


Run the app:

python app.py


Login with credentials:

Admin / admin

Cashier / cashier
## Requirements
- Python 3.x
- Tkinter (comes with Python)
- PIL (`pip install pillow`)

## Run
```bash
python app.py

