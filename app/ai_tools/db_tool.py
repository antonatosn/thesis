
"""Database tool for CrewAI chat agent to access SafeDrive Insurance database."""
from typing import Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from app import db
from app.models import Car, InsuranceProduct, Quote, User


class DatabaseToolInput(BaseModel):
    """Input schema for the DatabaseTool."""
    query_type: str = Field(..., description="The type of query to execute. Options: 'insurance_products', 'user_info', 'user_cars', 'user_quotes', 'quote_calculation', 'search_user', 'recent_quotes', 'general_quote', 'policy_details', 'search_cars', 'search_user_details'.")


class DatabaseTool(BaseTool):
    """Tool for chat agent to query the SafeDrive Insurance database."""

    name: str = "database_query"
    description: str = (
        "Access the SafeDrive Insurance database to retrieve information about "
        "users, cars, insurance products, and quotes. Use this tool to get "
        "real-time data to assist customers with their inquiries."
    )
    args_schema: Type[BaseModel] = DatabaseToolInput

    def _run(self, query_type: str, **kwargs) -> str:
        """
        Execute database queries based on query type.

        Args:
            query_type: Type of query to execute
            **kwargs: Additional parameters for the query

        Returns:
            String representation of query results
        """
        try:
            if query_type == "insurance_products":
                return self._get_insurance_products()
            elif query_type == "user_info":
                return self._get_user_info(kwargs.get("user_id"))
            elif query_type == "user_cars":
                return self._get_user_cars(kwargs.get("user_id"))
            elif query_type == "user_quotes":
                return self._get_user_quotes(kwargs.get("user_id"))
            elif query_type == "quote_calculation":
                return self._calculate_quote(
                    kwargs.get("car_id"),
                    kwargs.get("product_id")
                )
            elif query_type == "search_user":
                return self._search_user(kwargs.get("username"))
            elif query_type == "recent_quotes":
                return self._get_recent_quotes(kwargs.get("limit", 10))
            elif query_type == "general_quote":
                return self._get_general_quote(
                    kwargs.get("car_model"),
                    kwargs.get("driver_age")
                )
            elif query_type == "policy_details":
                return self._retrieve_policy_details(kwargs.get("policy_number"))
            elif query_type == "search_cars":
                return self._get_cars(
                    license_plate=kwargs.get("license_plate"),
                    make=kwargs.get("make"),
                    model=kwargs.get("model"),
                    mileage=kwargs.get("mileage"),
                    vehicle_value=kwargs.get("vehicle_value")
                )
            elif query_type == "search_user_details":
                return self._search_user_details(
                    license_plate=kwargs.get("license_plate"),
                    first_name=kwargs.get("first_name"),
                    last_name=kwargs.get("last_name")
                )
            else:
                return f"Unknown query type: {query_type}"
        except Exception as e:
            return f"Database error: {str(e)}"

    def _get_insurance_products(self) -> str:
        """Get all insurance products."""
        products = InsuranceProduct.query.order_by(
            InsuranceProduct.base_price).all()

        result = ["Available Insurance Products:"]
        for product in products:
            features = product.features.replace(', ', '\n  • ')
            result.append(
                f"\n{product.name} ({product.coverage_type})"
                f"\n  Base Price: €{product.base_price}/year"
                f"\n  Description: {product.description}"
                f"\n  Features:\n  • {features}"
            )

        return "\n".join(result)

    def _get_user_info(self, user_id: Optional[int]) -> str:
        """Get user information by ID."""
        if not user_id:
            return "User ID required"

        user = User.query.get(user_id)
        if not user:
            return f"User with ID {user_id} not found"

        return (
            f"User Information:\n"
            f"  Username: {user.username}\n"
            f"  Name: {user.first_name} {user.last_name}\n"
            f"  Email: {user.email}\n"
            f"  Phone: {user.phone}\n"
            f"  Member since: {user.created_at.strftime('%Y-%m-%d')}"
        )

    def _get_user_cars(self, user_id: Optional[int]) -> str:
        """Get all cars for a user."""
        if not user_id:
            return "User ID required"

        cars = Car.query.filter_by(user_id=user_id).order_by(
            Car.created_at.desc()).all()

        if not cars:
            return "No vehicles found for this user"

        result = ["User's Vehicles:"]
        for car in cars:
            result.append(
                f"\n  Car ID {car.id}: {car.year} {car.make} {car.model}"
                f"\n    License Plate: {car.license_plate}"
                f"\n    Value: €{car.vehicle_value:,}"
                f"\n    Mileage: {car.mileage:,} km"
                f"\n    Added: {car.created_at.strftime('%Y-%m-%d')}"
            )

        return "\n".join(result)

    def _get_user_quotes(self, user_id: Optional[int]) -> str:
        """Get all quotes for a user."""
        if not user_id:
            return "User ID required"

        quotes = db.session.query(
            Quote, Car.make, Car.model, Car.year, InsuranceProduct.name, InsuranceProduct.coverage_type
        ).join(
            Car, Quote.car_id == Car.id
        ).join(
            InsuranceProduct, Quote.product_id == InsuranceProduct.id
        ).filter(
            Quote.user_id == user_id
        ).order_by(
            Quote.created_at.desc()
        ).all()

        if not quotes:
            return "No quotes found for this user"

        result = ["User's Insurance Quotes:"]
        for quote, car_make, car_model, car_year, product_name, coverage_type in quotes:
            status_text = "Active" if quote.status == "active" else "Saved"
            result.append(
                f"\n  Quote ID {quote.id}: {car_year} {car_make} {car_model}"
                f"\n    Product: {product_name} ({coverage_type})"
                f"\n    Price: €{quote.price}/year"
                f"\n    Status: {status_text}"
                f"\n    Created: {quote.created_at.strftime('%Y-%m-%d %H:%M')}"
            )

        return "\n".join(result)

    def _search_user(self, username: Optional[str]) -> str:
        """Search for a user by username."""
        if not username:
            return "Username required"

        user = User.query.filter_by(username=username).first()
        if not user:
            return f"User '{username}' not found"

        return self._get_user_info(user.id)

    def _get_recent_quotes(self, limit: int = 10) -> str:
        """Get recent quotes across all users."""
        quotes = db.session.query(
            Quote, User.username, Car.make, Car.model, Car.year, InsuranceProduct.name
        ).join(
            User, Quote.user_id == User.id
        ).join(
            Car, Quote.car_id == Car.id
        ).join(
            InsuranceProduct, Quote.product_id == InsuranceProduct.id
        ).order_by(
            Quote.created_at.desc()
        ).limit(limit).all()

        if not quotes:
            return "No recent quotes found"

        result = [f"Recent {limit} Insurance Quotes:"]
        for quote, username, car_make, car_model, car_year, product_name in quotes:
            result.append(
                f"\n  {username}: {car_year} {car_make} {car_model}"
                f"\n    Product: {product_name} - €{quote.price}/year"
                f"\n    Date: {quote.created_at.strftime('%Y-%m-%d %H:%M')}"
            )

        return "\n".join(result)

    def _calculate_quote(self, car_id: Optional[int], product_id: Optional[int]) -> str:
        """Calculate a quote for a specific car and product."""
        if not car_id or not product_id:
            return "Car ID and Product ID required"

        car = Car.query.get(car_id)
        product = InsuranceProduct.query.get(product_id)

        if not car:
            return f"Car with ID {car_id} not found"
        if not product:
            return f"Product with ID {product_id} not found"

        # Use the same calculation logic from main.py
        import math

        base_price = float(product.base_price)
        car_value = float(car.vehicle_value)
        car_year = int(car.year)
        car_mileage = int(car.mileage)

        # Value factor
        value_factor = car_value / 15000

        # Age factor
        current_year = 2024
        car_age = current_year - car_year
        if car_age <= 3:
            age_factor = 0.9
        elif car_age <= 8:
            age_factor = 1.0
        else:
            age_factor = 1.0 + (car_age - 8) * 0.06
        age_factor = max(0.9, min(1.6, age_factor))

        # Mileage factor
        kilometers = car_mileage * 1.60934
        avg_annual_km = kilometers / car_age if car_age > 0 else kilometers
        if avg_annual_km < 15000:
            mileage_factor = 0.9
        elif avg_annual_km < 25000:
            mileage_factor = 1.0
        else:
            mileage_factor = 1.0 + ((avg_annual_km - 25000) / 10000) * 0.1
        mileage_factor = max(0.9, min(1.3, mileage_factor))

        # Calculate final price
        price = base_price * value_factor * age_factor * mileage_factor
        price = math.ceil(price / 5) * 5

        return (
            f"Quote Calculation for {car.year} {car.make} {car.model}:\n"
            f"  Product: {product.name} ({product.coverage_type})\n"
            f"  Base Price: €{base_price}\n"
            f"  Value Factor: {value_factor:.2f} (car value: €{car_value:,})\n"
            f"  Age Factor: {age_factor:.2f} (car age: {car_age} years)\n"
            f"  Mileage Factor: {mileage_factor:.2f} (avg: {avg_annual_km:,.0f} km/year)\n"
            f"  Final Price: €{price}/year"
        )

    def _get_general_quote(self, car_model: Optional[str], driver_age: Optional[int]) -> str:
        """Get a general insurance quote based on car model and driver age."""
        if not car_model or not driver_age:
            return "Car model and driver age are required for a general quote."

        try:
            age = int(driver_age)
        except (ValueError, TypeError):
            return "Invalid driver age provided. Please provide a number."

        # Simplified logic for a general quote
        base_price = 500  # Starting base price

        # Car risk factor
        car_risk_factor = 1.0
        if any(keyword in car_model.lower() for keyword in ["sport", "luxury", "convertible"]):
            car_risk_factor = 1.5
        elif any(keyword in car_model.lower() for keyword in ["suv", "truck"]):
            car_risk_factor = 1.2
        elif any(keyword in car_model.lower() for keyword in ["sedan", "hatchback"]):
            car_risk_factor = 1.0

        # Driver age factor
        if 18 <= age < 25:
            age_factor = 1.8
        elif 25 <= age < 30:
            age_factor = 1.4
        elif 30 <= age < 65:
            age_factor = 1.0
        else:
            age_factor = 1.2

        # Calculate final price
        price = base_price * car_risk_factor * age_factor

        return (
            f"General Insurance Quote Estimate:\n"
            f"  Car Model: {car_model}\n"
            f"  Driver Age: {age}\n"
            f"  Estimated Annual Premium: €{price:.2f}/year\n\n"
            f"Note: This is a non-binding estimate. For a precise quote, please provide more details about the specific vehicle."
        )

    def _retrieve_policy_details(self, policy_number: Optional[str]) -> str:
        """Retrieve policy details by policy number."""
        if not policy_number:
            return "Policy number is required to retrieve policy details."

        # Assuming policy_number is the quote ID for simplicity
        try:
            quote_id = int(policy_number)
        except (ValueError, TypeError):
            return "Invalid policy number format. Please provide a valid number."

        quote = db.session.query(Quote).filter_by(id=quote_id).first()

        if not quote:
            return f"Policy with number {policy_number} not found."

        user = User.query.get(quote.user_id)
        car = Car.query.get(quote.car_id)
        product = InsuranceProduct.query.get(quote.product_id)

        if not user or not car or not product:
            return "Could not retrieve all details for the policy."

        policy_details = (
            f"Policy Details for Policy #{policy_number}:\n"
            f"  Status: {quote.status.capitalize()}\n"
            f"  Created on: {quote.created_at.strftime('%Y-%m-%d')}\n\n"
        )

        owner_details = (
            f"Policy Owner Details:\n"
            f"  Name: {user.first_name} {user.last_name}\n"
            f"  Username: {user.username}\n"
            f"  Email: {user.email}\n"
            f"  Phone: {user.phone}\n\n"
        )

        vehicle_details = (
            f"Vehicle Details:\n"
            f"  Make and Model: {car.year} {car.make} {car.model}\n"
            f"  License Plate: {car.license_plate}\n"
            f"  Vehicle Value: €{car.vehicle_value:,}\n"
            f"  Mileage: {car.mileage:,} km\n\n"
        )

        product_details = (
            f"Insurance Product Details:\n"
            f"  Product Name: {product.name}\n"
            f"  Coverage Type: {product.coverage_type}\n"
            f"  Annual Premium: €{quote.price}/year\n"
        )

        return policy_details + owner_details + vehicle_details + product_details

    def _get_cars(self, license_plate: Optional[str] = None, make: Optional[str] = None, model: Optional[str] = None, mileage: Optional[int] = None, vehicle_value: Optional[int] = None) -> str:
        """Get cars based on license plate or other criteria."""
        if not any([license_plate, make, model, mileage, vehicle_value]):
            return "Please provide at least one search criterion: license_plate, make, model, mileage, or vehicle_value."

        query = Car.query

        if license_plate:
            cars = query.filter(Car.license_plate.ilike(f"%{license_plate}%")).all()
            if not cars:
                return f"No cars found with license plate containing '{license_plate}'."
        else:
            filters = []
            if make:
                filters.append(Car.make.ilike(f"%{make}%"))
            if model:
                filters.append(Car.model.ilike(f"%{model}%"))
            if mileage:
                try:
                    filters.append(Car.mileage <= int(mileage))
                except (ValueError, TypeError):
                    return "Invalid mileage provided. Please provide a number."
            if vehicle_value:
                try:
                    filters.append(Car.vehicle_value >= int(vehicle_value))
                except (ValueError, TypeError):
                    return "Invalid vehicle value provided. Please provide a number."

            if not filters:
                return "Please provide more specific criteria to search for a car."

            cars = query.filter(*[f for f in filters]).all()
            if not cars:
                return "No cars found matching the specified criteria."

        result = ["Found Cars:"]
        for car in cars:
            result.append(
                f"\n  Car ID {car.id}: {car.year} {car.make} {car.model}"
                f"\n    License Plate: {car.license_plate}"
                f"\n    Value: €{car.vehicle_value:,}"
                f"\n    Mileage: {car.mileage:,} km"
                f"\n    Owner User ID: {car.user_id}"
                f"\n    Added: {car.created_at.strftime('%Y-%m-%d')}"
            )

        return "\n".join(result)

    def _search_user_details(self, license_plate: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None) -> str:
        """Search for a user's details based on license plate, first name, or last name."""
        if not any([license_plate, first_name, last_name]):
            return "Please provide at least one search criterion: license_plate, first_name, or last_name."

        query = User.query
        
        if license_plate:
            query = query.join(Car).filter(Car.license_plate.ilike(f"%{license_plate}%"))

        if first_name:
            query = query.filter(User.first_name.ilike(f"%{first_name}%"))

        if last_name:
            query = query.filter(User.last_name.ilike(f"%{last_name}%"))

        users = query.all()

        if not users:
            return "No users found matching the specified criteria."

        result = ["Found Users:"]
        for user in users:
            result.append(self._get_user_info(user.id))
            result.append(self._get_user_cars(user.id))

        return "\n\n".join(result)