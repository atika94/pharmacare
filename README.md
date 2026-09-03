# pharmacare
A full-stack pharmacy management and medicine ordering system built with Python, Flask, HTML, CSS, and JavaScript, featuring inventory management, customer accounts, shopping cart, online ordering, and store pickup.
# Pharmacy Management System

A full-stack web-based Pharmacy Management System developed using **Python, Flask, HTML, CSS, and JavaScript**.

The system is designed to manage pharmacy inventory while also providing a customer-facing platform for browsing medicines, adding products to a shopping cart, placing orders, and selecting in-store pickup.

## Key Features

* Pharmacy inventory and medicine management
* Customer registration and authentication
* Role-based access for administrators and customers
* Medicine search and browsing
* Shopping cart functionality
* Customer medicine ordering
* Store pickup workflow
* Order status management
* Stock management and availability tracking
* Low-stock and expiry monitoring
* Order history for customers
* Administrative dashboard

## Technologies Used

* **Python** — Backend programming
* **Flask** — Web application framework
* **HTML5** — Page structure
* **CSS3** — User interface styling
* **JavaScript** — Frontend interactions
* **SQLite** — Lightweight relational database
* **python-dotenv** — Environment variable loading
* **Jinja2** — Server-side HTML templating
* **Git & GitHub** — Version control

## System Workflow

### Customer

Browse Medicines
       ↓
Add Medicine to Cart
       ↓
Review Cart
       ↓
Place Order
       ↓
Select Store Pickup
       ↓
Track Order Status
       ↓
Collect Medicine from Store

### Pharmacy Staff

Manage Medicines
       ↓
Manage Inventory
       ↓
Receive Customer Orders
       ↓
Confirm Order
       ↓
Prepare Order
       ↓
Mark as Ready for Pickup
       ↓
Complete Order

## Database

PharmaCare uses **SQLite** as its relational database. SQLite is included with Python, so no database server installation is required.

The Flask backend communicates with SQLite using Python's built-in `sqlite3` module:

```
sqlite3
```

No ORM is being used. All database operations are performed using direct SQL queries with parameterized statements to prevent SQL injection.

### Tables

| Table      | Description                                |
|------------|--------------------------------------------|
| `users`    | Stores customer and admin accounts         |
| `medicines`| Stores medicine inventory and details      |

### Environment Variables

The optional environment variable below controls the SQLite database file. **Never commit `.env` to version control.**

| Variable      | Description                    | Example         |
|---------------|--------------------------------|-----------------|
| `SQLITE_DB_PATH` | SQLite database file | `pharmacare.db` |
| `SECRET_KEY`     | Flask secret key     | *(random string)*|

## Setup & Running

### Prerequisites

* Python 3.10+

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/pharmacare.git
cd pharmacare
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```
SQLITE_DB_PATH=pharmacare.db
SECRET_KEY=your_secret_key_here
```

### 6. Run the Application

```bash
python run.py
```

Flask will start at: `http://127.0.0.1:5000`

The application automatically creates `pharmacare.db` and the required tables on first run.

## Project Status

**Currently in development**

The project is being developed incrementally:

- [x] Phase 1 — Flask application setup
- [x] Phase 2 — SQLite database integration
- [x] Phase 3 — Authentication (customer registration & login)
- [x] Phase 4 — Medicine browsing and search
- [x] Phase 5 — Shopping cart and ordering
- [ ] Phase 6 — Admin dashboard

## Author

Developed as a full-stack Python/Flask project for learning and portfolio development.