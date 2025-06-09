"""Flask application factory for the Flask web application."""
import os

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    """
    Create the Flask web application instance.
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=f"mysql+pymysql://{os.environ.get('MYSQL_USER', 'flask_user')}:{os.environ.get('MYSQL_PASSWORD', 'flask_password')}@{os.environ.get('MYSQL_HOST', 'localhost')}/{os.environ.get('MYSQL_DATABASE', 'flask_app')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Initialize SQLAlchemy with the app
    db.init_app(app)
    migrate.init_app(app=app, db=db)

    # Register blueprints
    from . import auth, main  # pylint: disable=import-outside-toplevel
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)

    # Register CLI commands
    @app.cli.command('seed')
    def seed_command():
        """Seeds the database with sample data."""
        from .models import Car  # pylint: disable=import-outside-toplevel
        from .models import (  # pylint: disable=import-outside-toplevel
            InsuranceProduct, Quote, User)

        # Check if we already have data to prevent re-seeding
        if InsuranceProduct.query.count() > 0:
            print('Database already seeded. Exiting.')
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

        # --- Add sample cars ---
        user1: User | None = User.query.filter_by(username='johndoe').first()
        user2: User | None = User.query.filter_by(username='janedoe').first()

        cars = [
            Car(user_id=user1.id, make='Volkswagen', model='Golf', year=2018,
                license_plate='181-D-12345', vehicle_value=18000.00, mileage=56000) if user1 else None,
            Car(user_id=user1.id, make='Hyundai', model='Tucson', year=2020,
                license_plate='201-C-54321', vehicle_value=26500.00, mileage=25000) if user1 else None,
            Car(user_id=user2.id, make='Skoda', model='Octavia', year=2019,
                license_plate='192-KY-98765', vehicle_value=22000.00, mileage=42000) if user2 else None
        ]
        db.session.bulk_save_objects(cars)
        db.session.commit()
        print("Sample cars added.")

        # --- Add sample quotes (with corrected car lookups) ---
        all_products = InsuranceProduct.query.all()
        car1:  Car | None = Car.query.filter_by(
            license_plate='181-D-12345').first()
        car2:  Car | None = Car.query.filter_by(
            license_plate='201-C-54321').first()
        car3:  Car | None = Car.query.filter_by(
            license_plate='192-KY-98765').first()

        quotes = [
            Quote(user_id=user1.id, car_id=car1.id,
                  product_id=all_products[0].id, price=550.00, status='pending') if user1 and car1 else None,
            Quote(user_id=user1.id, car_id=car1.id,
                  product_id=all_products[1].id, price=880.00, status='approved') if user1 and car1 else None,
            Quote(user_id=user1.id, car_id=car2.id,
                  product_id=all_products[2].id, price=1350.00, status='pending') if user1 and car2 else None,
            Quote(user_id=user2.id, car_id=car3.id,
                  product_id=all_products[1].id, price=920.00, status='approved') if user2 and car3 else None,
            Quote(user_id=user2.id, car_id=car3.id,
                  product_id=all_products[3].id, price=2100.00, status='pending') if user2 and car3 else None
        ]
        db.session.bulk_save_objects(quotes)
        db.session.commit()
        print("Sample quotes added.")
        print("Database initialized successfully with sample data.")

    return app
