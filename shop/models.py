from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from __init__ import db
from __init__ import app

class User(db.Model):
    __tablename__ = 'users'  # Change the table name as needed

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.Integer, default=0)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    #def __init__(self, name, email, password):
      #  self.name = name
       # self.email = email
       # self.password = password

    def __repr__(self):
        return f"<User('{self.name}', '{self.email}')>"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(100))

    cart_items = db.relationship('CartItem', back_populates='product')

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'),  nullable=False)
    username = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255))

    # Establish a many-to-one relationship with Product
    product = db.relationship('Product', back_populates='cart_items')


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    adinfo = db.Column(db.String(255), nullable=False)
    image_filename = db.Column(db.String(255))
    phone = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    street = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    zip = db.Column(db.String(100), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    street = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    zip = db.Column(db.String(100), nullable=False)
    payment = db.Column(db.String(100), nullable=False)
    total = db.Column(db.Integer)
    message = db.Column(db.String(100), default='None')
    status = db.Column(db.String(100), default='pending')
    s_indicator = db.Column(db.String(100), default='pending')
    image_filename = db.Column(db.String(255), nullable=True)
    ordertime = db.Column(db.DateTime, default=datetime.utcnow)
    arrival = db.Column(db.DateTime, nullable=True)

class Shipping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    shippedWith = db.Column(db.String(100), nullable=False)
    estimatedArrival = db.Column(db.String(100), nullable=False)
    

class OrderProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    sellername = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(255))
    ratings = db.Column(db.Integer, nullable=True)

class Erp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0)
    payable = db.Column(db.Float, nullable=False, default=0)
    receivable = db.Column(db.Float, nullable=False, default=0)

class Payout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    ammount = db.Column(db.Float, nullable=False)
    gcash = db.Column(db.String(255), nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(100), default='pending')



with app.app_context():
    db.create_all()