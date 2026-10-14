from flask import Blueprint, request, session, jsonify
from models import db, Category, Expense
from . import login_required

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    user_id = session['user_id']
    cat_type = request.args.get('type')  # 'expense' or 'income'

    query = Category.query.filter(
        (Category.user_id == None) | (Category.user_id == user_id)
    )

    if cat_type in ('expense', 'income'):
        query = query.filter(Category.type == cat_type)

    categories = query.order_by(Category.is_default.desc(), Category.name.asc()).all()
    return jsonify([cat.to_dict() for cat in categories])

@categories_bp.route('/api/categories', methods=['POST'])
@login_required
def create_category():
    user_id = session['user_id']
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    cat_type = data.get('type', 'expense').lower()
    icon = data.get('icon', 'tag').strip()
    color = data.get('color', '#6366f1').strip()

    if not name:
        return jsonify({'error': 'Category name is required.'}), 400
    if cat_type not in ('expense', 'income'):
        return jsonify({'error': 'Type must be "expense" or "income".'}), 400

    # Check duplicate for this user
    existing = Category.query.filter(
        (Category.name.ilike(name)),
        ((Category.user_id == user_id) | (Category.user_id == None)),
        (Category.type == cat_type)
    ).first()

    if existing:
        return jsonify({'error': f'Category "{name}" already exists.'}), 400

    category = Category(
        user_id=user_id,
        name=name,
        type=cat_type,
        icon=icon,
        color=color,
        is_default=False
    )
    db.session.add(category)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Category created successfully!', 'category': category.to_dict()}), 201

@categories_bp.route('/api/categories/<int:cat_id>', methods=['DELETE'])
@login_required
def delete_category(cat_id):
    user_id = session['user_id']
    category = Category.query.filter_by(id=cat_id, user_id=user_id).first()

    if not category:
        return jsonify({'error': 'Custom category not found or cannot delete system default categories.'}), 404

    # Check if category is used in expenses
    usage_count = Expense.query.filter_by(category_id=cat_id).count()
    if usage_count > 0:
        return jsonify({'error': f'Cannot delete category because it is linked to {usage_count} expense transaction(s). Please reassign them first.'}), 400

    db.session.delete(category)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Category deleted successfully!'})
