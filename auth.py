import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Category
from . import login_required

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.view_dashboard'))

    if request.method == 'POST':
        # Supports both form submission and JSON
        data = request.get_json(silent=True) or request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        currency = data.get('currency', 'USD').upper()

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        if not email or not is_valid_email(email):
            errors.append('Please provide a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if confirm_password and password != confirm_password:
            errors.append('Passwords do not match.')

        if User.query.filter_by(username=username).first():
            errors.append('Username is already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email is already registered.')

        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html', username=username, email=email)

        # Create user
        user = User(username=username, email=email, currency=currency)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Log in newly registered user
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session['currency'] = user.currency
        session.permanent = True

        if request.is_json:
            return jsonify({'success': True, 'message': 'Registration successful!', 'user': user.to_dict()}), 201

        flash('Registration successful! Welcome to your financial dashboard.', 'success')
        return redirect(url_for('dashboard.view_dashboard'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.view_dashboard'))

    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        login_identifier = data.get('login', '').strip() # can be email or username
        password = data.get('password', '')
        remember = data.get('remember', False)

        if not login_identifier or not password:
            error = 'Please enter both username/email and password.'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'danger')
            return render_template('login.html', login_identifier=login_identifier)

        user = User.query.filter(
            (User.email == login_identifier.lower()) | (User.username == login_identifier)
        ).first()

        if not user or not user.check_password(password):
            error = 'Invalid email/username or password.'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 401
            flash(error, 'danger')
            return render_template('login.html', login_identifier=login_identifier)

        # Success - establish session
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session['currency'] = user.currency
        if remember:
            session.permanent = True

        if request.is_json:
            return jsonify({'success': True, 'message': 'Login successful!', 'user': user.to_dict()}), 200

        next_page = request.args.get('next')
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page or url_for('dashboard.view_dashboard'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile_page():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@auth_bp.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    user = User.query.get(session['user_id'])
    data = request.get_json() or {}

    new_username = data.get('username', '').strip()
    new_currency = data.get('currency', '').strip().upper()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if new_username and new_username != user.username:
        if User.query.filter(User.username == new_username, User.id != user.id).first():
            return jsonify({'error': 'Username is already taken.'}), 400
        user.username = new_username
        session['username'] = new_username

    if new_currency:
        user.currency = new_currency
        session['currency'] = new_currency

    if new_password:
        if not current_password or not user.check_password(current_password):
            return jsonify({'error': 'Current password is required and must be correct.'}), 400
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters.'}), 400
        user.set_password(new_password)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Profile updated successfully!', 'user': user.to_dict()})

@auth_bp.route('/api/auth/me')
@login_required
def current_user():
    user = User.query.get(session['user_id'])
    return jsonify(user.to_dict())
