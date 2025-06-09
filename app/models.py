"""Models for the insurance application."""
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model):
    """Represents a user in the system.

    Attributes:
        id (int): The primary key for the user.
        username (str): The user's unique username.
        password (str): The user's hashed password.
        email (str): The user's unique email address.
        first_name (str, optional): The user's first name.
        last_name (str, optional): The user's last name.
        phone (str, optional): The user's phone number.
        created_at (datetime): The timestamp when the user was created.
        cars (relationship): A relationship to the Car model, representing cars owned by the user.
                             Cascades all operations and deletes orphans.
        quotes (relationship): A relationship to the Quote model, representing quotes associated with the user.
                              Cascades all operations and deletes orphans.

    Methods:
        __init__(username, password, email, first_name=None, last_name=None, phone=None):
            Initializes a new User instance.
        set_password(password):
            Hashes the provided password and sets it for the user.
        check_password(password):
            Checks if the provided password matches the stored hashed password.
        __repr__():
            Returns a string representation of the User object.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username:  str = db.Column(db.String(100), unique=True, nullable=False)
    password:  str = db.Column(db.String(255), nullable=False)
    email:  str = db.Column(db.String(100), unique=True, nullable=False)
    first_name:  str = db.Column(db.String(100))
    last_name:  str = db.Column(db.String(100))
    phone:  str = db.Column(db.String(20))
    created_at: datetime = db.Column(
        db.DateTime, default=datetime.now(timezone.utc))

    # Relationships
    cars = db.relationship('Car', backref='owner',
                           lazy=True, cascade="all, delete-orphan")
    quotes = db.relationship('Quote', backref='user',
                             lazy=True, cascade="all, delete-orphan")

    def __init__(self, username, password, email, first_name='', last_name='', phone=''):
        self.username = username
        self.set_password(password)
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone

    def set_password(self, password):
        """
        Hash the provided password and set it for the user.
        Args:
            password (str): The plaintext password to hash.
        """
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """
        Check if the provided password matches the stored hashed password.

        Args:
            password (str): The plaintext password to verify.

        Returns:
            bool: True if the password matches the stored hash, False otherwise.
        """
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Car(db.Model):
    """Represents a car owned by a user.
    Attributes:
        id (int): The primary key for the car.
        user_id (int): The ID of the user who owns the car.
        make (str): The make of the car.
        model (str): The model of the car.
        year (int): The year of manufacture of the car.
        license_plate (str): The license plate number of the car.
        vehicle_value (float): The estimated value of the car.
        mileage (int): The mileage of the car in kilometers or miles.
        created_at (datetime): The timestamp when the car was created.
        quotes (relationship): A relationship to the Quote model, representing quotes associated with the car.
                             Cascades all operations and deletes orphans.
    Methods:
        __init__(user_id, make, model, year, license_plate, vehicle_value, mileage):
            Initializes a new Car instance.
        __repr__():
            Returns a string representation of the Car object.
    """
    __tablename__ = 'cars'

    id:  int = db.Column(db.Integer, primary_key=True)
    user_id:  int = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False)
    make:  str = db.Column(db.String(100), nullable=False)
    model:  str = db.Column(db.String(100), nullable=False)
    year:  int = db.Column(db.Integer, nullable=False)
    license_plate:  str = db.Column(db.String(20), nullable=False)
    vehicle_value:  float = db.Column(db.Float, nullable=False)
    mileage:  int = db.Column(db.Integer, nullable=False)
    created_at: datetime = db.Column(
        db.DateTime, default=datetime.now(timezone.utc))

    def __init__(self, user_id, make, model, year, license_plate, vehicle_value, mileage):
        """
        Initializes a new Car instance.

        Args:
            user_id (int): The ID of the user who owns the car.
            make (str): The make of the car.
            model (str): The model of the car.
            year (int): The year of manufacture of the car.
            license_plate (str): The license plate number of the car.
            vehicle_value (float): The estimated value of the car.
            mileage (int): The mileage of the car in kilometers or miles.
        """
        self.user_id = user_id
        self.make = make
        self.model = model
        self.year = year
        self.license_plate = license_plate
        self.vehicle_value = vehicle_value
        self.mileage = mileage
        self.created_at = datetime.now(timezone.utc)

    # Relationships
    quotes = db.relationship('Quote', backref='car',
                             lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Car {self.make} {self.model} ({self.year})>'


class InsuranceProduct(db.Model):
    """Represents an insurance product.
    Attributes:
        id (int): The primary key for the insurance product.
        name (str): The name of the insurance product.
        description (str): A description of the insurance product.
        coverage_type (str): The type of coverage provided by the insurance product.
        base_price (float): The base price of the insurance product.
        features (str): A list of features included in the insurance product.
        quotes (relationship): A relationship to the Quote model, representing quotes associated with the insurance product.
    Methods:
        __init__(name, description, coverage_type, base_price, features):
            Initializes a new InsuranceProduct instance.
        __repr__():
            Returns a string representation of the InsuranceProduct object.
    """
    __tablename__ = 'insurance_products'

    id:  int = db.Column(db.Integer, primary_key=True)
    name:  str = db.Column(db.String(100), nullable=False)
    description:  str = db.Column(db.Text, nullable=False)
    coverage_type:  str = db.Column(db.String(50), nullable=False)
    base_price:  float = db.Column(db.Float, nullable=False)
    features:  str = db.Column(db.Text, nullable=False)

    # Relationships
    quotes = db.relationship('Quote', backref='product', lazy=True)

    def __init__(self, name, description, coverage_type, base_price, features):
        """
        Initializes a new InsuranceProduct instance.

        Args:
            name (str): The name of the insurance product.
            description (str): A description of the insurance product.
            coverage_type (str): The type of coverage provided by the insurance product.
            base_price (float): The base price of the insurance product.
            features (str): A list of features included in the insurance product.
        """
        self.name = name
        self.description = description
        self.coverage_type = coverage_type
        self.base_price = base_price
        self.features = features

    def __repr__(self):
        return f'<InsuranceProduct {self.name}>'


class Quote(db.Model):
    """Represents a quote for an insurance product.
    Attributes:
        id (int): The primary key for the quote.
        user_id (int): The ID of the user who requested the quote.
        car_id (int): The ID of the car associated with the quote.
        product_id (int): The ID of the insurance product associated with the quote.
        price (float): The quoted price for the insurance product.
        status (str): The status of the quote (e.g., 'pending', 'accepted', 'rejected').
        created_at (datetime): The timestamp when the quote was created.
    Methods:
        __init__(user_id, car_id, product_id, price, status='pending'):
            Initializes a new Quote instance.
        __repr__():
            Returns a string representation of the Quote object.
    """
    __tablename__ = 'quotes'

    id:  int = db.Column(db.Integer, primary_key=True)
    user_id:  int = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False)
    car_id:   int = db.Column(
        db.Integer, db.ForeignKey('cars.id'), nullable=False)
    product_id:  int = db.Column(db.Integer, db.ForeignKey(
        'insurance_products.id'), nullable=False)
    price:  float = db.Column(db.Float, nullable=False)
    status:  str = db.Column(db.String(20), default='pending')
    created_at: datetime = db.Column(
        db.DateTime, default=datetime.now(timezone.utc))

    def __init__(self, user_id, car_id, product_id, price, status='pending'):
        self.user_id = user_id
        self.car_id = car_id
        self.product_id = product_id
        self.price = price
        self.status = status

    def __repr__(self):
        return f'<Quote #{self.id} - ${self.price}>'
