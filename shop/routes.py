from flask import Flask, flash, abort
from __init__ import app, db, bcrypt, allowed_file, ITEMS_PER_PAGE
from shop.forms import RegistrationForm, Loginform, AddProductForm, AddProfile
from shop.models import User, Product, CartItem, Profile, Order, OrderProduct, Shipping, Erp, Payout
from flask import render_template, session, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from flask_paginate import Pagination, get_page_args
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime


@app.route('/')
def dashboard():
    page = request.args.get('page', 1, type=int)

    # Fetch all products and convert the query to a list
    products = Product.query.all()

    username = session.get('name')
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)


    pagination = Pagination(page=page, total=len(products), per_page=ITEMS_PER_PAGE, css_framework='bootstrap4')

    # Use pagination.page to get the current page number
    products_on_page = products[pagination.page * pagination.per_page - pagination.per_page: pagination.page * pagination.per_page]

    return render_template('users/index.html', products=products_on_page, pagination=pagination, cart_items=cart_items, total_items=total_items)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'name' in session:
        username = session.get('name')
        flash(f'{username} you are already logged in', 'danger')
        return redirect(url_for('dashboard'))

    form = Loginform()
    if request.method == "POST" and form.validate():
        user = User.query.filter_by(name=form.name.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.role == 3:
                flash('Account banned. Please contact support.', 'danger')
                return redirect(url_for('login'))

            session['name'] = form.name.data

            # Check if an Erp record already exists for the user
            existing_erp = Erp.query.filter_by(username=form.name.data).first()

            if not existing_erp:
                # Create a new Erp record for the user with default values
                new_erp = Erp(username=form.name.data, balance=0.0, payable=0.0, receivable=0.0)
                db.session.add(new_erp)
                db.session.commit()

            if user.role != 0:
                return redirect(url_for('admin'))
            else:
                return redirect(request.args.get('next') or url_for('dashboard'))
        else:
            flash('Invalid name or password', 'danger')

    return render_template('users/login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate():
        # Check if the 'name' is already in use
        existing_user_by_name = User.query.filter_by(name=form.name.data).first()

        # Check if the 'email' is already in use
        existing_user_by_email = User.query.filter_by(email=form.email.data).first()

        if existing_user_by_name:
            flash('Registration failed. The name is already in use.', 'danger')
        elif existing_user_by_email:
            flash('Registration failed. The email is already in use.', 'danger')
        else:
            hash_password = bcrypt.generate_password_hash(form.password.data)
            user = User(name=form.name.data, email=form.email.data, password=hash_password)
            db.session.add(user)
            db.session.commit()
            flash('Thank you for Registering. Please Login.', 'success')
            return redirect(url_for('login'))

    return render_template('users/register.html', form=form)


@app.route('/logout', methods=['GET'])
def logout():
    if 'name' in session:
        session.clear()
        flash('You are now logged out', 'success')
    else:
        flash('You are not logged in', 'info')

    return redirect(url_for('dashboard'))

@app.route('/shop-grid')
def shopgrid():
    username = session.get('name')
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)
    return render_template('users/shop-grid.html', cart_items=cart_items, total_items=total_items)

@app.route('/shop-details/<int:id>')
def shopdetails(id):
    username = session.get('name')
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)

    product = Product.query.get_or_404(id)

    # Fetching average ratings for the product
    avg_ratings = OrderProduct.query.with_entities(func.avg(OrderProduct.ratings).label('avg_ratings'),
                                                   func.count(OrderProduct.ratings).label('total_ratings')) \
        .filter(OrderProduct.product_id == id, OrderProduct.ratings.isnot(None), OrderProduct.ratings != 0).first()

    # If there are ratings, use the average and total count; otherwise, set them to None
    average_ratings = avg_ratings[0] if avg_ratings[0] is not None else None
    total_ratings_count = avg_ratings[1] if avg_ratings[1] is not None else None

    return render_template('users/shop-details.html', product=product, cart_items=cart_items, total_items=total_items,
                           average_ratings=average_ratings, total_ratings_count=total_ratings_count)
    

@app.route('/shop-cart')
def shopcart():
    if 'name' not in session:
        flash('please login first', 'danger')
        return redirect(url_for('login'))
    
    username = session.get('name')
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)

    # Calculate the total price
    cart_total = sum(cart_item.price * cart_item.quantity for cart_item in cart_items)
    return render_template('users/shoping-cart.html', cart_items=cart_items, cart_total=cart_total, total_items=total_items)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'name' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        username = session.get('name')
        current_page_url = request.form.get('current_page_url')

        # Fetch the product from your database using the product_id
        product = Product.query.get(product_id)

        if product and quantity <= product.stock:
            # Check if the product belongs to the user
            if product.username == username:
                flash("Action Not Allowed", 'danger')
            else:
                # Create a cart item with the product's details, including the image_filename
                cart_item = CartItem(
                    product_id=product.id,
                    name=product.name,
                    username=username,
                    description=product.description,
                    quantity=quantity,
                    price=product.price,
                    image_filename=product.image_filename
                )
                flash('Product added to cart', 'success')
                db.session.add(cart_item)
                db.session.commit()

        elif not product:
            flash('Product not found', 'error')
        else:
            flash('Quantity exceeds available stock', 'danger')

    # Redirect to the current page if the addition was successful or not allowed
    return redirect(current_page_url)


from flask import flash

@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'name' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action', '')
        error_occurred = False  # Flag to track if any errors occurred during the update

        if action == 'update':
            for key, value in request.form.items():
                if key.startswith('cart_item_') and key.endswith('_quantity'):
                    item_id = int(key.split('_')[2])
                    new_quantity = int(value)

                    cart_item = CartItem.query.get(item_id)

                    if cart_item:
                        if new_quantity <= cart_item.product.stock:
                            cart_item.quantity = new_quantity
                            db.session.commit()
                        else:
                            error_occurred = True
                            flash(f'New quantity for {cart_item.product.name} exceeds available stock', 'danger')

            if not error_occurred:
                flash('Cart updated successfully', 'success')
        elif action.startswith('delete'):
            # Handle delete logic for a specific item
            selected_item_id = int(action.split('_')[1])
            cart_item = CartItem.query.get(selected_item_id)

            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
                flash('Cart item deleted successfully', 'success')

    return redirect(url_for('shopcart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'name' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    username = session.get('name')
    profile = Profile.query.filter_by(username=username).first()
    cart_items = CartItem.query.filter_by(username=username).all()
    cart_total = sum(cart_item.price * cart_item.quantity for cart_item in cart_items)
    total_items = len(cart_items)

    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        phone = request.form.get('phone')
        street = request.form.get('street')
        city = request.form.get('city')
        message = request.form.get('message')
        state = request.form.get('state')
        zip_code = request.form.get('zip')
        payment_method = request.form.get('paymentMethod')
        total_amount = request.form.get('total')

        # Check if there are items in the cart before creating OrderProduct instances
        if cart_items:
            # Create a dictionary to store products based on sellers
            products_by_seller = {}

            # Group cart items by seller
            for cart_item in cart_items:
                seller_name = cart_item.product.username

                if seller_name not in products_by_seller:
                    products_by_seller[seller_name] = []

                products_by_seller[seller_name].append(cart_item)

            try:
                # Create separate orders for each seller
                for seller_name, seller_cart_items in products_by_seller.items():
                    order = Order(
                        username=session['name'],
                        name=name,
                        phone=phone,
                        street=street,
                        message=message,
                        city=city,
                        state=state,
                        zip=zip_code,
                        payment=payment_method,
                        total=sum(cart_item.price * cart_item.quantity for cart_item in seller_cart_items),
                        status='pending',
                        image_filename=profile.image_filename
                    )

                    db.session.add(order)
                    db.session.commit()

                    # Create OrderProduct instances and associate them with the order and cart items
                    for cart_item in seller_cart_items:
                        product = Product.query.filter_by(id=cart_item.product_id).first()
                        product_price = cart_item.price * cart_item.quantity
                        order_product = OrderProduct(
                            order_id=order.id,
                            product_id=cart_item.product_id,
                            product=cart_item.name,
                            sellername=seller_name,
                            price=product_price,
                            image_filename=cart_item.image_filename,
                            quantity=cart_item.quantity
                        )
                        db.session.add(order_product)
                        db.session.commit()

                # Clear the cart after placing the order
                CartItem.query.filter_by(username=username).delete()
                db.session.commit()

                flash('Order placed successfully!', 'success')
                return redirect(url_for('checkout'))  # Redirect to a success or another appropriate route

            except Exception as e:
                db.session.rollback()
                flash('An error occurred while placing the order: ' + str(e), 'danger')

        else:
            flash('Cannot place an order with an empty cart', 'danger')

    # Render the checkout form template for GET requests
    return render_template('users/checkout.html', cart_items=cart_items, cart_total=cart_total, profile=profile, total_items=total_items)




@app.route('/accept_order/<int:id>', methods=['GET', 'POST'])
def accept_order(id):
    # Fetch the order from the database
    order = Order.query.get(id)

    if order:
        # Fetch ordered products for the given order
        ordered_products = OrderProduct.query.filter_by(order_id=order.id).all()

        # Check if there is sufficient stock for each ordered product
        for ordered_product in ordered_products:
            product = Product.query.get(ordered_product.product_id)
            if not product or product.stock < ordered_product.quantity:
                flash(f'Insufficient stock for product {product.name}', 'error')
                return redirect(url_for('sellerpage'))

        # Update the status and s_indicator
        order.status = 'accepted'
        order.s_indicator = 'moving'

        # Update product stock and Erp entries based on ordered products
        for ordered_product in ordered_products:
            product = Product.query.get(ordered_product.product_id)

            # Update product stock
            product.stock -= ordered_product.quantity

            # Update receivable in Erp model
            erp = Erp.query.filter_by(username=product.username).first()
            if erp:
                erp.receivable += (ordered_product.quantity * product.price)
            else:
                # Create an Erp entry if it doesn't exist
                new_erp = Erp(username=product.username)
                new_erp.receivable = (ordered_product.quantity * product.price)
                db.session.add(new_erp)

        # Fetch Erp entry for the product's username
        erp = Erp.query.filter_by(username=product.username).first()

        # Update balance in Erp model
        if erp:
            erp.balance = erp.receivable + erp.payable

        # Commit the changes to the database
        db.session.commit()

        # Flash a success message
        flash('Order has been accepted', 'success')

    # Redirect to the page where the orders are displayed
    return redirect(url_for('sellerpage'))


@app.route('/to_ship/<int:id>', methods=['GET', 'POST'])
def ship_order(id):
    # Fetch the order from the database
    order = Order.query.get(id)

    if not order:
        # Redirect to an error page if the order is not found
        return render_template('error_page.html', message='Order not found')

    if request.method == 'POST':
        # If the form is submitted
        shipped_with = request.form.get('shippedWith')
        estimated_arrival = request.form.get('estimatedArrival')

        # Create a new Shipping record in the database
        new_shipping = Shipping(order_id=order.id, shippedWith=shipped_with, estimatedArrival=estimated_arrival)
        db.session.add(new_shipping)

        # Update the status and s_indicator
        order.status = 'deliver'
        order.s_indicator = 'moving'

        # Commit the changes to the database
        db.session.commit()

        flash('Order Status and Shipping Information have been updated', 'success')
        return redirect(url_for('sellerpage'))

    # If it's a GET request, display the form
    return render_template('shipping.html', order=order)

@app.route('/cancel_ship/<int:id>', methods=['GET', 'POST'])
def cancel_ship(id):
    # Fetch the order from the database
    order = Order.query.get(id)

    if order:
        # Check if the order was previously accepted
        if order.status == 'accepted':
            # Revert the status and s_indicator
            order.status = 'pending'
            order.s_indicator = 'pending'

            # Fetch ordered products for the given order
            ordered_products = OrderProduct.query.filter_by(order_id=order.id).all()

            # Revert product stock and Erp entries based on ordered products
            for ordered_product in ordered_products:
                product = Product.query.get(ordered_product.product_id)

                # Revert product stock
                product.stock += ordered_product.quantity

                # Revert receivable in Erp model
                erp = Erp.query.filter_by(username=product.username).first()
                if erp:
                    erp.receivable -= (ordered_product.quantity * product.price)

            # Fetch Erp entry for the product's username
            erp = Erp.query.filter_by(username=product.username).first()

            # Revert balance in Erp model
            if erp:
                erp.balance = erp.receivable + erp.payable

        # Commit the changes to the database
        db.session.commit()

        # Flash a success message
        flash('Order Status has been reverted', 'success')

    # Redirect to the page where the orders are displayed
    return redirect(url_for('sellerpage'))


@app.route('/mark_delivered/<int:id>', methods=['GET', 'POST'])
def mark_delivered(id):
    # Fetch the order from the database
    order = Order.query.get(id)

    if order:
        # Update the status and s_indicator
        order.status = 'delivered'
        order.s_indicator = 'moving'

        # Fetch ordered products for the given order
        ordered_products = OrderProduct.query.filter_by(order_id=order.id).all()

        # Update product stock and receivable based on ordered products
        for ordered_product in ordered_products:
            product = Product.query.get(ordered_product.product_id)
            if product:
                # Update product stock

                # Update payable in Erp model
                erp = Erp.query.filter_by(username=product.username).first()
                if erp:
                    erp.payable += (ordered_product.quantity * product.price)
                    erp.receivable -= (ordered_product.quantity * product.price)
                else:
                    # Create an Erp entry if it doesn't exist
                    new_erp = Erp(username=product.username)
                    new_erp.payable = (ordered_product.quantity * product.price)
                    new_erp.receivable = - (ordered_product.quantity * product.price)
                    db.session.add(new_erp)

        # Fetch Erp entry for the product's username
        erp = Erp.query.filter_by(username=product.username).first()

        # Update balance in Erp model
        if erp:
            erp.balance = erp.receivable + erp.payable

        # Commit the changes to the database
        db.session.commit()

        # Flash a success message
        flash('Order Status has been updated', 'success')

    # Redirect to the page where the orders are displayed
    return redirect(url_for('sellerpage'))


@app.route('/mark_received/<int:id>', methods=['GET', 'POST'])
def mark_received(id):
    # Fetch the order from the database
    order = Order.query.get(id)

    if request.method == 'POST':
        # Update the status and s_indicator
        order.status = 'received'
        order.s_indicator = 'moving'

        # Update arrival to the current time
        order.arrival = datetime.utcnow()

        # Update ratings based on the submitted form data
        rating = int(request.form.get('rating', 0))

        # Fetch all OrderProduct records with the same order_id
        order_products = OrderProduct.query.filter_by(order_id=order.id).all()

        # Update ratings in all associated OrderProduct records
        for order_product in order_products:
            order_product.ratings = rating

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('tracking', order_id=order.id))

@app.route('/ratings/<int:id>')
def ratings(id):
    order = Order.query.get(id)

    return render_template('ratings.html', order=order)




@app.route('/deny_order/<int:id>', methods=['GET', 'POST'])
def deny_order(id):
    # Fetch the order from the database
    order = Order.query.get(id)
    if order:
        # Update the status and s_indicator
        order.status = 'denied'
        order.s_indicator = 'cancelled'

        # Commit the changes to the database
        db.session.commit()
        flash('Order denied', 'success')
    # Redirect to the page where the orders are displayed
    return redirect(url_for('sellerpage'))

@app.route('/profile')
def profile():
    if 'name' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))

    username = session.get('name')
    profile = Profile.query.filter_by(username=username).first()
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)

    # Fetch all products for the user
    products = Product.query.filter_by(username=username).all()

    # Use get_page_args to get the current page number from the request args
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')

    # Set a fixed number of items per page (e.g., 9 items)
    per_page = 9

    # Calculate the range of products for the current page
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    products_on_page = products[start_index:end_index]

    # Create pagination object
    pagination = Pagination(page=page, total=len(products), per_page=per_page, css_framework='bootstrap4')

    return render_template('users/profile.html', cart_items=cart_items, total_items=total_items, products=products_on_page, pagination=pagination, profile=profile)

@app.route('/sellerpage')
def sellerpage():
    if 'name' not in session:
        flash('please login first', 'danger')
        return redirect(url_for('login'))

    if 'name' in session:
        users= User.query
    
    username = session.get('name')
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)
    
    erp = Erp.query.filter_by(username=username).first()
    # Join the Order and OrderProduct tables on the order_id and id fields
    orders = (
        db.session.query(Order)
        .join(OrderProduct, Order.id == OrderProduct.order_id)
        .filter(OrderProduct.sellername == username)
        .order_by(desc(OrderProduct.id))  # Order by the id in descending order
        .all()
    )

    return render_template('seller/index.html', orders=orders, total_items=total_items, cart_items=cart_items, erp=erp)


@app.route('/sellerproducts')
def sellerproducts():
    if 'name' not in session:
        flash('please login first', 'danger')
        return redirect(url_for('login'))
    
    username = session.get('name')
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)
    products = Product.query.filter_by(username=username).all()
    return render_template('seller/products.html', products = products, cart_items=cart_items, total_items=total_items)

@app.route('/add-products', methods=['GET', 'POST'])
def addproducts():
    if 'name' not in session:
        flash('please login first', 'danger')
        return redirect(url_for('login'))
    
    user = session.get('name')
    cart_items = CartItem.query.filter_by(username=user).all()
    total_items = len(cart_items)
    form = AddProductForm()

    if request.method == "POST":
        if form.validate():

            username = session.get('name')
            name = form.name.data
            description = form.description.data
            category = form.category.data
            price = form.price.data
            stock = form.stock.data

            product = Product(username=username, name=name, description=description, category=category, price=price, stock=stock)

            product_image = form.product_image.data
            if product_image and allowed_file(product_image.filename):
                # Save the image file and update the image_filename field
                image_filename =  product_image.filename
                product_image.save(os.path.join(app.config['UPLOAD_FOLDER']) + image_filename)
                product.image_filename = image_filename

                try:
                    db.session.add(product)  # Add the Product object to the session
                    db.session.commit()  # Commit the transaction to save the data to the database
                    flash("Product added successfully", "success")
                    return redirect(url_for('addproducts'))  # Replace 'your_success_route' with the actual success route
                except Exception as e:
                    db.session.rollback()
                    flash("An error occurred while adding the product: " + str(e), "error")
            else:
                flash("Invalid file type for product image", "error")
        else:
            flash("Invalid Input", "error")

    return render_template('seller/add-product.html', form=form, cart_items=cart_items, total_items=total_items)

@app.route('/edit-products/<int:product_id>', methods=['GET', 'POST'])
def editproducts(product_id):
    username = session.get('name')
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)

    form = AddProductForm()
    product = Product.query.get(product_id)

    if request.method == 'POST':
        # Get the updated data from the form
        product.name = request.form['name']
        product.category = request.form['category']
        product.description = request.form['description']
        product.price = request.form['price']
        product.stock = request.form['stock']

        product_image = request.files['product_image']
        if product_image and allowed_file(product_image.filename):
            image_filename = product_image.filename
            product_image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            product.image_filename = image_filename

        # Update related CartItem records
        cart_items = CartItem.query.filter_by(product_id=product.id).all()
        for cart_item in cart_items:
            cart_item.name = product.name
            cart_item.description = product.description
            cart_item.price = product.price
            # Update other fields as needed
            if product_image:  # Check if a new image is provided
                cart_item.image_filename = image_filename

        db.session.commit()

        flash('Product updated successfully', 'success')
        return redirect(url_for('editproducts', product_id=product.id))

    return render_template('seller/edit-product.html', product=product, form=form, cart_items=cart_items, total_items=total_items)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'name' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    
    # Check if a profile with the given username already exists
    username = session.get('name')
    existing_profile = Profile.query.filter_by(username=username).first()
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)

    form = AddProfile(obj=existing_profile)

    if request.method == "POST":
        if form.validate_on_submit():
            name = form.name.data
            adinfo = form.adinfo.data
            phone = form.phone.data
            street = form.street.data
            state = form.state.data
            city = form.city.data
            zip_code = form.zip.data

            if existing_profile:
                # If the profile exists, update its fields
                existing_profile.name = name
                existing_profile.adinfo = adinfo
                existing_profile.street = street
                existing_profile.state = state
                existing_profile.phone = phone
                existing_profile.city = city
                existing_profile.zip = zip_code

                # Check if a new image is provided
                image_file = form.product_image.data
                if image_file and allowed_file(image_file.filename):
                    # Save the new image file
                    image_filename = secure_filename(image_file.filename)
                    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                    existing_profile.image_filename = image_filename

                try:
                    db.session.commit()  # Commit the transaction to save the updated data
                    flash("Profile updated successfully", "success")
                    return redirect(url_for('settings'))  # Redirect to a success or another appropriate route
                except Exception as e:
                    db.session.rollback()
                    flash("An error occurred while updating the profile: " + str(e), "error")
            else:
                # If the profile doesn't exist, create a new one
                profile = Profile(
                    username=username,
                    name=name,
                    adinfo=adinfo,
                    street=street,
                    state=state,
                    phone=phone,
                    city=city,
                    zip=zip_code
                )

                # Check if an image is provided
                image_file = form.product_image.data
                if image_file and allowed_file(image_file.filename):
                    # Save the image file
                    image_filename = secure_filename(image_file.filename)
                    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                    profile.image_filename = image_filename

                try:
                    db.session.add(profile)
                    db.session.commit()
                    flash("Profile added successfully", "success")
                    return redirect(url_for('settings'))  # Redirect to a success or another appropriate route
                except Exception as e:
                    db.session.rollback()
                    flash("An error occurred while adding the profile: " + str(e), "error")

    return render_template('users/settings.html', form=form, existing_profile=existing_profile, total_items=total_items)


@app.route('/order-products/<int:order_id>')
def order_products(order_id):
    if 'name' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    username = session.get('name')
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)

    # Query the Order and associated OrderProducts
    order = (
        db.session.query(Order)
        .filter(Order.id == order_id, OrderProduct.sellername == username)
        .first()
    )

    if not order:
        flash('Order not found or unauthorized access', 'danger')
        return redirect(url_for('sellerpage'))

    # Query OrderProducts for the specified order_id, Order id, and sellername
    order_products = (
        db.session.query(OrderProduct)
        .join(Product, OrderProduct.product_id == Product.id)
        .filter(OrderProduct.order_id == order_id, Order.id == order_id, OrderProduct.sellername == username)
        .all()
    )

    return render_template('seller/see-details.html', order=order, order_products=order_products, total_items=total_items)

        
@app.route('/terms-and-conditions')
def terms():
    return render_template('users/terms-and-conditions.html')

@app.route('/my-orders', methods=['GET'])
def vieworders():
    # Check if the user is logged in
    if 'name' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))

    # Get the username from the session
    username = session.get('name')
    cart_items = CartItem.query.filter_by(username=username).all()
    total_items = len(cart_items)

    # Set the page and items per page
    page = request.args.get('page', 1, type=int)
    per_page = 3  # Adjust this value as needed

    # Paginate the user orders
    user_orders_pagination = (
        db.session.query(OrderProduct, Order)
        .join(Order, Order.id == OrderProduct.order_id)
        .filter(Order.username == username)
        .order_by(desc(OrderProduct.id))
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template('users/view-orders.html', user_orders_pagination=user_orders_pagination, username=username, total_items=total_items)

@app.route('/tracking')
def tracking():
    # Retrieve the order_id from the query parameters
    order_id = request.args.get('order_id', type=int)

    # Check if the user is logged in
    if 'name' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login')) 

    username = session.get('name')
    order = (
        db.session.query(Order)
        .filter(Order.id == order_id, Order.username == username)
        .first()
    )
    
    shipping = (
    db.session.query(Shipping)
    .filter(Shipping.order_id == order_id)  # Assuming shipping_id is the ID you are looking for
    .first()
)

    
    if order:
        return render_template('trackingmodal.html', order=order, shipping=shipping)
    else:
        flash('Order not found or does not belong to the logged-in user', 'danger')
        return redirect(url_for('some_redirect_route'))  # Replace with an appropriate route
    

@app.route('/delete_orderproduct/<int:orderproduct_id>')
def del_orderproduct(orderproduct_id):
    try:
        # Fetch the OrderProduct entry by id
        order_product = OrderProduct.query.get_or_404(orderproduct_id)

        # Check if the corresponding order has a status of 'accepted'
        order_status = Order.query.filter(Order.id == order_product.order_id).value(Order.status)
        if order_status != 'pending':
            flash('Order has been accepted and cannot be deleted.', 'danger')
            return redirect(url_for('vieworders'))

        # Get the order_id from the OrderProduct entry
        order_id = order_product.order_id

        # Delete the OrderProduct entry
        db.session.delete(order_product)
        db.session.commit()

        # Check if there are no more OrderProduct entries with the same order_id
        remaining_order_products = OrderProduct.query.filter_by(order_id=order_id).count()

        # If there are no more OrderProduct entries, delete the corresponding Order entry
        if remaining_order_products == 0:
            order = Order.query.get(order_id)
            db.session.delete(order)
            db.session.commit()

        flash('OrderProduct deleted successfully', 'success')
        return redirect(url_for('vieworders'))

    except NoResultFound:
        # Handle case when no order_product is found by the given id
        flash('OrderProduct not found. Please try again.', 'danger')
        return redirect(url_for('vieworders'))
    except IntegrityError:
        # Handle any integrity errors (e.g., foreign key constraint violation)
        flash('Error deleting OrderProduct. Please try again.', 'danger')
        return redirect(url_for('vieworders'))

@app.route('/admin')
def admin():
    # Fetch the list of users from the User model
    users = User.query.all()

    # Fetch the list of products from the Product model
    products = Product.query.all()

    # Fetch the list of payout requests from the Payout model
    payout_requests = Payout.query.all()


    admin_erp = Erp.query.filter_by(username='admin').first()

    total_balance = db.session.query(func.sum(Erp.balance)).filter(Erp.username != 'admin').scalar()

    pending_payout = db.session.query(func.coalesce(func.sum(Payout.ammount), 0.0)).filter(Payout.status == 'pending').scalar() 

    # Pass the 'users', 'products', and 'payout_requests' variables to the template
    return render_template('admin/admin.html', users=users, products=products, payout_requests=payout_requests, admin_erp=admin_erp, total_balance=total_balance, pending_payout=pending_payout)



@app.route('/ban_user/<int:user_id>', methods=['POST'])
def ban_user(user_id):
    user = User.query.get(user_id)

    if user:
        # Update user role to '3' (banned)
        user.role = 3
        db.session.commit()
        flash(f'User {user.name} has been banned.', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('admin'))  # Redirect back to the admin page

@app.route('/unban_user/<int:user_id>', methods=['POST'])
def unban_user(user_id):
    user = User.query.get(user_id)

    if user:
        # Update user role to '0' (regular user)
        user.role = 0
        db.session.commit()
        flash(f'User {user.name} has been unbanned.', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('admin'))



@app.route('/payout', methods=['GET', 'POST'])
def payout():
    username = session.get('name')
    erp_user = Erp.query.filter_by(username=username).first()
    available = erp_user.payable - 1000  # Define available outside the conditional block

    if request.method == 'POST':
        amount_to_payout = float(request.form.get('amount'))
        gcash_number = request.form.get('gcash')

        if erp_user:
            # Check if the balance is above 700 and if the requested payout won't bring it below 700
            if erp_user.balance <= 700 or (erp_user.balance - amount_to_payout) < 700:
                flash('Balance is not sufficient for payout.', 'danger')
            else:
                # Calculate 10% of the payout amount to deduct
                deduction_amount = 0.10 * amount_to_payout

                # Deduct 10% from the payout amount
                payout_amount_after_deduction = amount_to_payout - deduction_amount

                # Update Erp model
                erp_user.payable -= amount_to_payout
                erp_user.balance -= amount_to_payout

                # Update or create the admin record
                admin_erp = Erp.query.filter_by(username='admin').first()
                if admin_erp:
                    admin_erp.receivable += deduction_amount
                    admin_erp.balance += amount_to_payout  # Add the deducted amount to admin's balance
                else:
                    admin_erp = Erp(username='admin', receivable=deduction_amount, balance=payout_amount_after_deduction)
                    db.session.add(admin_erp)

                # Create Payout record
                payout_record = Payout(username=username, ammount=payout_amount_after_deduction, gcash=gcash_number)
                db.session.add(payout_record)

                db.session.commit()

                flash('Cashout request successful!', 'success')
                return redirect(url_for('sellerpage'))
        else:
            flash('Invalid username. Please check your session and try again.', 'error')

    return render_template('seller/payout.html', erp_user=erp_user, available=available)




@app.route('/upload_proof/<int:payout_id>', methods=['GET', 'POST'])
def upload_proof(payout_id):
    # Check if the form is submitted using POST
    if request.method == 'POST':
        # Get the uploaded file
        proof_image = request.files['proof']

        # Check if a file was provided
        if proof_image:
            # Save the file to a secure location (you may need to configure this)
            proof_image_filename = secure_filename(proof_image.filename)
            proof_image.save(os.path.join(app.config['UPLOAD_FOLDER'], proof_image_filename))

            # Update the Payout record with the image filename and status
            payout = Payout.query.get_or_404(payout_id)

            # Check if the admin's balance is sufficient
            admin_erp = Erp.query.filter_by(username='admin').first()
            if admin_erp and admin_erp.balance >= payout.ammount:
                # Deduct the amount from admin's balance
                admin_erp.balance -= payout.ammount

                payout.image_filename = proof_image_filename
                payout.status = 'Paid'

                # Commit the changes to the database
                db.session.commit()

                flash('Proof of payment uploaded successfully!', 'success')
            else:
                flash('Insufficient funds in admin\'s balance!', 'danger')
                # Optionally, you can redirect to a different page or take other actions here

        else:
            flash('No file uploaded!', 'danger')

    # Redirect back to the admin page after processing the form
    return redirect(url_for('admin'))





@app.route('/transactions')
def transactions():
    # Retrieve the username from the session
    username = session.get('name')

    # Fetch transactions for the current user from the database in descending order of id
    payouts_from_db = Payout.query.filter_by(username=username).order_by(desc(Payout.id)).all()

    return render_template('seller/transactions.html', payouts=payouts_from_db)
