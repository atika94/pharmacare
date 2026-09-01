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
* **MySQL** — Relational database
* **mysql-connector-python** — MySQL driver (no ORM)
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

PharmaCare uses **MySQL** as its relational database.

The Flask backend communicates with MySQL using:

```
mysql-connector-python
```

No ORM is being used. All database operations are performed using direct SQL queries with parameterized statements to prevent SQL injection.

### Tables

| Table      | Description                                |
|------------|--------------------------------------------|
| `users`    | Stores customer and admin accounts         |
| `medicines`| Stores medicine inventory and details      |

### Environment Variables

The following environment variables must be set before running the application. Copy `.env.example` to `.env` and fill in your actual values. **Never commit `.env` to version control.**

| Variable      | Description                    | Example         |
|---------------|--------------------------------|-----------------|
| `DB_HOST`     | MySQL server hostname          | `localhost`     |
| `DB_PORT`     | MySQL server port              | `3306`          |
| `DB_USER`     | MySQL username                 | `root`          |
| `DB_PASSWORD` | MySQL password                 | *(your password)*|
| `DB_NAME`     | MySQL database name            | `pharmacare`    |
| `SECRET_KEY`  | Flask secret key               | *(random string)*|

## Setup & Running

### Prerequisites

* Python 3.10+
* MySQL Server installed and running
* MySQL Workbench (optional, for GUI access)

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

### 4. Create MySQL Database

Open MySQL Workbench or MySQL CLI and run:

```sql
CREATE DATABASE pharmacare;
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=pharmacare
SECRET_KEY=your_secret_key_here
```

### 6. Run the Application

```bash
python run.py
```

Flask will start at: `http://127.0.0.1:5000`

The application will automatically create the required database tables on first run.

## Project Status

**Currently in development**

The project is being developed incrementally:

- [x] Phase 1 — Flask application setup
- [x] Phase 2 — MySQL database integration
- [ ] Phase 3 — Authentication (customer registration & login)
- [ ] Phase 4 — Medicine browsing and search
- [ ] Phase 5 — Shopping cart and ordering
- [ ] Phase 6 — Admin dashboard

## Author

Developed as a full-stack Python/Flask project for learning and portfolio development.