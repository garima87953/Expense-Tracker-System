from datetime import date
from flask import Blueprint, render_template, request, session, jsonify
from sqlalchemy import func, extract
from models import db, User, Budget, Category, Expense
from . import login_required

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/budgets')
@login_required
def view_budgets():
    user = User.query.get(session['user_id'])
    categories = Category.query.filter(
        (Category.user_id == None) | (Category.user_id == user.id),
        Category.type == 'expense'
    ).order_by(Category.name.asc()).all()
    return render_template('budgets.html', user=user, categories=categories)

@budgets_bp.route('/api/budgets', methods=['GET'])
@login_required
def get_budgets():
    user_id = session['user_id']
    month_year = request.args.get('month_year', date.today().strftime('%Y-%m'))

    # Parse year and month
    try:
        parts = month_year.split('-')
        year = int(parts[0])
        month = int(parts[1])
    except (ValueError, IndexError):
        return jsonify({'error': 'Invalid month_year format. Use YYYY-MM.'}), 400

    # Fetch configured budgets for this month
    budgets = Budget.query.filter_by(user_id=user_id, month_year=month_year).all()

    # Overall monthly spending
    total_spent_this_month = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == user_id,
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).scalar()

    # Category-wise spending
    cat_spent_query = db.session.query(
        Expense.category_id,
        func.coalesce(func.sum(Expense.amount), 0).label('spent')
    ).filter(
        Expense.user_id == user_id,
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).group_by(Expense.category_id).all()
    cat_spent_map = {cat_id: float(spent) for cat_id, spent in cat_spent_query}

    budget_items = []
    overall_budget_item = None

    for b in budgets:
        limit_val = float(b.amount)
        if b.category_id is None:
            # Overall budget
            spent_val = float(total_spent_this_month)
            remaining_val = limit_val - spent_val
            pct = round((spent_val / limit_val * 100), 1) if limit_val > 0 else 0.0
            status = 'danger' if pct >= 100 else ('warning' if pct >= 80 else 'safe')

            overall_budget_item = {
                'id': b.id,
                'category_id': None,
                'category_name': 'Total Monthly Budget',
                'category_color': '#6366f1',
                'category_icon': 'credit-card',
                'limit': limit_val,
                'spent': spent_val,
                'remaining': remaining_val,
                'percentage': pct,
                'status': status,
                'month_year': b.month_year
            }
        else:
            spent_val = cat_spent_map.get(b.category_id, 0.0)
            remaining_val = limit_val - spent_val
            pct = round((spent_val / limit_val * 100), 1) if limit_val > 0 else 0.0
            status = 'danger' if pct >= 100 else ('warning' if pct >= 80 else 'safe')

            budget_items.append({
                'id': b.id,
                'category_id': b.category_id,
                'category_name': b.category.name if b.category else 'Unknown',
                'category_color': b.category.color if b.category else '#6366f1',
                'category_icon': b.category.icon if b.category else 'tag',
                'limit': limit_val,
                'spent': spent_val,
                'remaining': remaining_val,
                'percentage': pct,
                'status': status,
                'month_year': b.month_year
            })

    return jsonify({
        'month_year': month_year,
        'overall_budget': overall_budget_item,
        'category_budgets': budget_items,
        'total_spent_month': float(total_spent_this_month)
    })

@budgets_bp.route('/api/budgets', methods=['POST'])
@login_required
def set_budget():
    user_id = session['user_id']
    data = request.get_json() or {}

    amount = data.get('amount')
    category_id = data.get('category_id') # None or int
    month_year = data.get('month_year', date.today().strftime('%Y-%m'))

    if not amount or float(amount) <= 0:
        return jsonify({'error': 'Budget amount must be greater than 0.'}), 400

    parsed_cat_id = int(category_id) if category_id and str(category_id).isdigit() else None

    # Upsert budget
    budget = Budget.query.filter_by(
        user_id=user_id,
        category_id=parsed_cat_id,
        month_year=month_year
    ).first()

    if budget:
        budget.amount = round(float(amount), 2)
        message = 'Budget updated successfully!'
    else:
        budget = Budget(
            user_id=user_id,
            category_id=parsed_cat_id,
            amount=round(float(amount), 2),
            month_year=month_year
        )
        db.session.add(budget)
        message = 'Budget created successfully!'

    db.session.commit()
    return jsonify({'success': True, 'message': message, 'budget': budget.to_dict()}), 201

@budgets_bp.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=session['user_id']).first()
    if not budget:
        return jsonify({'error': 'Budget not found.'}), 404

    db.session.delete(budget)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Budget removed successfully!'})
