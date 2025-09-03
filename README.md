# E-Commerce Website (Flask + Python)

A dynamic and scalable E-commerce platform built with the **Flask** framework and **Python**, supporting two distinct user roles: **Super Admin** and **User**.  
This application enables users to both buy and sell products, while giving administrators full oversight and control.

---

## User Roles & Features

### Super Admin
- Account: admin1 / 12341234
- Monitor and manage all registered users  
- View all products listed by users  
- Impose and manage payment requirements  
- Oversee platform activity and enforce policies  

### User
- Browse available products  
- Purchase items directly through the platform  
- List and manage their own products for sale  

---

## Tech Stack

- **Backend Framework**: Flask  
- **Programming Language**: Python  
- **Database**: SQLite / PostgreSQL (configurable)  
- **Frontend**: HTML, CSS, JavaScript (Jinja2 templating)  
- **Authentication**: Flask-Login

## Live Link
- **Adenan Grocery**: https://dikitanan21.pythonanywhere.com/

---

## Getting Started

To run the project locally:

```bash
# Clone the repository
git clone https://github.com/your-username/ecommerce-flask.git
cd ecommerce-flask

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
flask run
