"""Flask application factory for the Flask web application."""
import os

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize SQLAlchemy and Migrate extensions
# These are initialized here but will be bound to the app in the factory
db = SQLAlchemy()
migrate = Migrate()

# Global variable to hold the Flask app instance (singleton pattern)
_flask_app: Flask | None = None


def create_app():
    """
    Create and configure the Flask web application instance.

    This function implements a singleton pattern to ensure that the app
    is only created once.
    """
    global _flask_app

    # If the app has already been created, return the existing instance.
    if _flask_app is not None:
        return _flask_app

    # Create the app instance
    app = Flask(__name__, instance_relative_config=True)

    # --- IMPORTANT ---
    # Assign the app to the global variable immediately after creation.
    # This prevents the `UnboundLocalError` if a circular import (see below)
    # causes this function to be called recursively.
    _flask_app = app

    # Load configuration from environment variables with defaults
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'a-secure-default-secret-key'),
        SQLALCHEMY_DATABASE_URI=f"mysql+pymysql://{os.environ.get('MYSQL_USER', 'flask_user')}:{os.environ.get('MYSQL_PASSWORD', 'flask_password')}@{os.environ.get('MYSQL_HOST', 'localhost')}/{os.environ.get('MYSQL_DATABASE', 'flask_app')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app=app, db=db)

    # It's good practice to work within an application context when
    # dealing with extensions and CLI commands.
    with app.app_context():
        from . import auth, main
        app.register_blueprint(auth.bp)
        app.register_blueprint(main.bp)

        # Register custom CLI commands
        register_commands(app)

    return app


def register_commands(app: Flask):
    """Register CLI commands with the Flask app."""

    @app.cli.command('seed')
    def seed_command():
        """Seeds the database with sample data."""
        # Imports are placed here as they are only needed for this command
        # and require the application context to be available.
        from .models import Car, InsuranceProduct, Quote, User

        # Check if data exists to prevent re-seeding
        if InsuranceProduct.query.first():
            print('Database appears to be already seeded. Aborting.')
            return

        print('Seeding database with sample data...')

        # --- Add sample insurance products ---
        products = [
            InsuranceProduct(name='Third Party Only', description='Basic legal minimum cover...',
                             coverage_type='basic', base_price=400.00, features='Third party liability...'),
            InsuranceProduct(name='Third Party, Fire & Theft', description='Standard protection with coverage...',
                             coverage_type='standard', base_price=700.00, features='All Third Party features...'),
            InsuranceProduct(name='Comprehensive', description='Full protection for your vehicle...',
                             coverage_type='premium', base_price=1100.00, features='All Fire & Theft features...'),
            InsuranceProduct(name='Prestige Cover', description='Premium protection with maximum benefits...',
                             coverage_type='elite', base_price=1600.00, features='All Comprehensive features...')
        ]
        db.session.bulk_save_objects(products)
        db.session.commit()
        print("Insurance products added.")

        # --- Add sample users ---
        users = [
            User(username='johndoe', password='password', email='john.doe@example.com',
                 first_name='John', last_name='Doe', phone='555-123-4567'),
            User(username='janedoe', password='password', email='jane.doe@example.com',
                 first_name='Jane', last_name='Doe', phone='555-987-6543')
        ]
        db.session.bulk_save_objects(users)
        db.session.commit()
        print("Sample users added.")

        # --- Add sample cars (robustly) ---
        user1 = User.query.filter_by(username='johndoe').first()
        user2 = User.query.filter_by(username='janedoe').first()
        cars_to_add = []
        if user1:
            cars_to_add.extend([
                Car(user_id=user1.id, make='Volkswagen', model='Golf', year=2018,
                    license_plate='181-D-12345', vehicle_value=18000.00, mileage=56000),
                Car(user_id=user1.id, make='Hyundai', model='Tucson', year=2020,
                    license_plate='201-C-54321', vehicle_value=26500.00, mileage=25000)
            ])
        if user2:
            cars_to_add.append(
                Car(user_id=user2.id, make='Skoda', model='Octavia', year=2019,
                    license_plate='192-KY-98765', vehicle_value=22000.00, mileage=42000)
            )
        if cars_to_add:
            db.session.bulk_save_objects(cars_to_add)
            db.session.commit()
            print("Sample cars added.")

        # --- Add sample quotes (robustly) ---
        all_products = InsuranceProduct.query.all()
        car1 = Car.query.filter_by(license_plate='181-D-12345').first()
        car2 = Car.query.filter_by(license_plate='201-C-54321').first()
        car3 = Car.query.filter_by(license_plate='192-KY-98765').first()
        quotes_to_add = []

        if user1 and car1 and len(all_products) > 1:
            quotes_to_add.extend([
                Quote(user_id=user1.id, car_id=car1.id, product_id=all_products[0].id, price=550.00, status='pending'),
                Quote(user_id=user1.id, car_id=car1.id, product_id=all_products[1].id, price=880.00, status='approved')
            ])
        if user1 and car2 and len(all_products) > 2:
            quotes_to_add.append(
                Quote(user_id=user1.id, car_id=car2.id, product_id=all_products[2].id, price=1350.00, status='pending')
            )
        if user2 and car3 and len(all_products) > 3:
            quotes_to_add.extend([
                Quote(user_id=user2.id, car_id=car3.id, product_id=all_products[1].id, price=920.00, status='approved'),
                Quote(user_id=user2.id, car_id=car3.id, product_id=all_products[3].id, price=2100.00, status='pending')
            ])

        if quotes_to_add:
            db.session.bulk_save_objects(quotes_to_add)
            db.session.commit()
            print("Sample quotes added.")

        print("Database initialized successfully with sample data.")
