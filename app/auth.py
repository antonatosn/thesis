"""Authentication routes for the application."""
# app/auth.py
import functools
from typing import Callable, Optional

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)

from app import db
from app.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view: Callable) -> Callable:
    """
    A decorator to enforce that a user must be logged in to access a specific view.

    This decorator checks if the `g.user` object is `None`, indicating that no user is 
    currently logged in. If no user is logged in, it redirects the client to the login 
    page. Otherwise, it allows the wrapped view function to execute.

    Args:
        view (Callable): The view function to be wrapped by the decorator.

    Returns:
        Callable: The wrapped view function with login enforcement.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.route('/register', methods=('GET', 'POST'))
def register():
    """Register a new user."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'
        elif not first_name:
            error = 'First name is required.'
        elif not last_name:
            error = 'Last name is required.'
        elif not phone:
            error = 'Phone number is required.'

        if error is None:
            try:
                user = User(
                    username=username,
                    password=password,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone
                )
                db.session.add(user)
                db.session.commit()
                flash('Registration successful! Please log in.')
                return redirect(url_for('auth.login'))
            except Exception as e:
                error = f"Registration failed: {e}"

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """Log in an existing user."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        user: Optional[User] = User.query.filter_by(username=username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not user.check_password(password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id  # type: ignore
            return redirect(url_for('main.index'))

        flash(error)

    return render_template('auth/login.html')


@bp.route('/profile/edit', methods=('GET', 'POST'))
@login_required
def edit_profile():
    """Edit the logged-in user's profile."""
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        error = None

        if not email:
            error = 'Email is required.'
        elif not first_name:
            error = 'First name is required.'
        elif not last_name:
            error = 'Last name is required.'
        elif not phone:
            error = 'Phone is required.'

        if error is None:
            try:
                user: Optional[User] = User.query.get(g.user.id)
                if user is None:
                    error = 'User not found.'
                    return flash(error)
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.phone = phone
                db.session.commit()
                flash('Profile updated successfully!')
                return redirect(url_for('main.profile'))
            except Exception as e:
                error = f"Update failed: {e}"

        flash(error)

    return render_template('auth/edit_profile.html')


@bp.before_app_request
def load_logged_in_user():
    """Load the logged-in user into the global context."""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))
