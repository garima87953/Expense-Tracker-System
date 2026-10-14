from functools import wraps
from flask import session, redirect, url_for, request, jsonify

def login_required(f):
    """Decorator to require login for page views and API routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # If the request expects JSON or is an API route, return 401 JSON
            if request.path.startswith('/api/') or request.is_json:
                return jsonify({'error': 'Unauthorized. Please log in.'}), 401
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
