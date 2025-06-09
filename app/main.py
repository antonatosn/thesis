"""Main module for the insurance application."""
import math

from flask import (Blueprint, Response, flash, g, jsonify, redirect,
                   render_template, request, url_for)

from app import chat, db
from app.auth import login_required
from app.models import Car, InsuranceProduct, Quote

bp = Blueprint('main', __name__)
AGENT = chat.AgentCrew().create_crew()


@bp.route('/')
def index():
    """Home page showing insurance products and features."""
    products = InsuranceProduct.query.order_by(
        InsuranceProduct.base_price).all()
    return render_template('main/index.html', products=products)


@bp.route('/products')
def products():
    """Page showing all insurance products in detail."""
    products = InsuranceProduct.query.order_by(
        InsuranceProduct.base_price).all()
    return render_template('main/products.html', products=products)


@bp.route('/profile')
@login_required
def profile():
    """User profile page showing user details and their cars."""
    # Get user's cars
    cars = Car.query.filter_by(user_id=g.user.id).order_by(
        Car.created_at.desc()).all()

    # Get user's quotes with joined data
    quotes = db.session.query(
        Quote, Car.make, Car.model, Car.year, InsuranceProduct.name, InsuranceProduct.coverage_type
    ).join(
        Car, Quote.car_id == Car.id
    ).join(
        InsuranceProduct, Quote.product_id == InsuranceProduct.id
    ).filter(
        Quote.user_id == g.user.id
    ).order_by(
        Quote.created_at.desc()
    ).all()

    return render_template('main/profile.html', cars=cars, quotes=quotes)


@bp.route('/cars/add', methods=('GET', 'POST'))
@login_required
def add_car():
    """Add a new car to user's profile."""
    if request.method == 'POST':
        make = request.form['make']
        model = request.form['model']
        year = request.form['year']
        license_plate = request.form['license_plate']
        vehicle_value = request.form['vehicle_value']
        mileage = request.form['mileage']
        error = None

        if not make:
            error = 'Make is required.'
        elif not model:
            error = 'Model is required.'
        elif not year:
            error = 'Year is required.'
        elif not license_plate:
            error = 'License plate is required.'
        elif not vehicle_value:
            error = 'Vehicle value is required.'
        elif not mileage:
            error = 'Mileage is required.'

        if error is not None:
            flash(error)
        else:
            car = Car(
                user_id=g.user.id,
                make=make,
                model=model,
                year=year,
                license_plate=license_plate,
                vehicle_value=vehicle_value,
                mileage=mileage
            )
            db.session.add(car)
            db.session.commit()

            flash('Car added successfully!')
            return redirect(url_for('main.get_quotes', car_id=car.id))

    return render_template('main/add_car.html')


@bp.route('/cars/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit_car(id):
    """Edit an existing car."""
    car = Car.query.filter_by(id=id, user_id=g.user.id).first()

    if car is None:
        flash('Car not found or you do not have permission to edit it.')
        return redirect(url_for('main.profile'))

    if request.method == 'POST':
        make = request.form['make']
        model = request.form['model']
        year = request.form['year']
        license_plate = request.form['license_plate']
        vehicle_value = request.form['vehicle_value']
        mileage = request.form['mileage']
        error = None

        if not make:
            error = 'Make is required.'
        elif not model:
            error = 'Model is required.'
        elif not year:
            error = 'Year is required.'
        elif not license_plate:
            error = 'License plate is required.'
        elif not vehicle_value:
            error = 'Vehicle value is required.'
        elif not mileage:
            error = 'Mileage is required.'

        if error is not None:
            flash(error)
        else:
            car.make = make
            car.model = model
            car.year = year
            car.license_plate = license_plate
            car.vehicle_value = vehicle_value
            car.mileage = mileage

            db.session.commit()

            flash('Car updated successfully!')
            return redirect(url_for('main.profile'))

    return render_template('main/edit_car.html', car=car)


@bp.route('/cars/<int:id>/delete', methods=('POST',))
@login_required
def delete_car(id):
    """Delete a car."""
    car = Car.query.filter_by(id=id, user_id=g.user.id).first()

    if car is not None:
        # The quotes will be automatically deleted due to the cascade relationship
        db.session.delete(car)
        db.session.commit()
        flash('Car deleted successfully!')

    return redirect(url_for('main.profile'))


@bp.route('/cars/<int:car_id>/quotes')
@login_required
def get_quotes(car_id):
    """Get insurance quotes for a specific car."""
    car = Car.query.filter_by(id=car_id, user_id=g.user.id).first()

    if car is None:
        flash('Car not found or you do not have permission to view it.')
        return redirect(url_for('main.profile'))

    # Get insurance products
    products = InsuranceProduct.query.order_by(
        InsuranceProduct.base_price).all()

    # Calculate quotes based on car details and products
    quotes = []
    for product in products:
        # Irish market pricing algorithm based on car value, year, and mileage
        base_price = float(product.base_price)
        car_value = float(car.vehicle_value)
        car_year = int(car.year)
        car_mileage = int(car.mileage)

        # Adjust based on car value (higher value = higher premium)
        # Irish insurance is particularly sensitive to car value
        value_factor = car_value / 15000  # €15,000 car has factor of 1.0

        # Adjust based on car age (Irish insurers typically charge more for older cars)
        current_year = 2024
        car_age = current_year - car_year
        # Newer cars (0-3 years) get better rates
        if car_age <= 3:
            age_factor = 0.9
        # Mid-age cars (4-8 years) get standard rates
        elif car_age <= 8:
            age_factor = 1.0
        # Older cars (9+ years) get higher rates
        else:
            # 6% increase per year over 8 years
            age_factor = 1.0 + (car_age - 8) * 0.06

        # Limit between 0.9 and 1.6
        age_factor = max(0.9, min(1.6, age_factor))

        # Adjust based on mileage (Irish market typically uses kilometers)
        # Convert mileage to km (approximate)
        kilometers = car_mileage * 1.60934

        # Low km (<15,000 km/year since manufacture) gets discount
        avg_annual_km = kilometers / car_age if car_age > 0 else kilometers
        if avg_annual_km < 15000:
            mileage_factor = 0.9
        # Normal km (15,000-25,000 km/year) gets standard rate
        elif avg_annual_km < 25000:
            mileage_factor = 1.0
        # High km (>25,000 km/year) gets higher rate
        else:
            # 10% per 10,000 km over 25,000
            mileage_factor = 1.0 + ((avg_annual_km - 25000) / 10000) * 0.1

        mileage_factor = max(0.9, min(1.3, mileage_factor)
                             )  # Limit between 0.9 and 1.3

        # Calculate final price and convert to euros
        price = base_price * value_factor * age_factor * mileage_factor
        price = math.ceil(price / 5) * 5  # Round up to nearest €5

        quotes.append({
            'product_id': product.id,
            'product_name': product.name,
            'coverage_type': product.coverage_type,
            'description': product.description,
            'features': product.features.split(', '),
            'price': price
        })

    return render_template('main/quotes.html', car=car, quotes=quotes)


@bp.route('/quotes/save', methods=('POST',))
@login_required
def save_quote():
    """Save a quote to the database."""
    car_id = request.form['car_id']
    product_id = request.form['product_id']
    price = request.form['price']

    # Check if car belongs to user
    car = Car.query.filter_by(id=car_id, user_id=g.user.id).first()

    if car is None:
        flash('Car not found or you do not have permission to save quotes for it.')
        return redirect(url_for('main.profile'))

    # Check if product exists
    product = InsuranceProduct.query.get(product_id)

    if product is None:
        flash('Invalid insurance product.')
        return redirect(url_for('main.get_quotes', car_id=car_id))

    # Save the quote
    quote = Quote(
        user_id=g.user.id,
        car_id=car_id,
        product_id=product_id,
        price=price
    )
    db.session.add(quote)
    db.session.commit()

    flash('Quote saved successfully!')
    return redirect(url_for('main.profile'))


@bp.route("/chat", methods=('POST',))
def chat_ai() -> Response:
    """
    Handles chatAI interactions by processing user messages and generating responses.

    This function retrieves a user message from the incoming JSON request, processes
    it using the `customer_rep` chat model, and returns the generated response in a
    JSON format. It also includes user authentication context.

    Returns:
        Response: A JSON response containing the generated reply to the user's message.
    """
    user_message = request.json.get("message", "") if request.json else ""
    
    # Check user authentication status and prepare context
    if g.user is not None:
        user_context = f"AUTHENTICATED USER: {g.user.username} (ID: {g.user.id}, Name: {g.user.first_name} {g.user.last_name})"
        full_message = f"{user_context}\n\nUser message: {user_message}"
    else:
        user_context = "GUEST USER: Not logged in"
        full_message = f"{user_context}\n\nUser message: {user_message}"
    
    # add user message with context to Task
    response = AGENT.kickoff(
        inputs={"user_message": full_message})  # Process with CrewAI
    return jsonify({"response": response.raw}) if response else Response(
        "No response generated.", status=500
    )
