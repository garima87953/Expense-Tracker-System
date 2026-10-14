from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, session, jsonify, redirect, url_for, request
from sqlalchemy import func, extract
from models import db, User, Expense, Income, Category, Budget
from . import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.view_dashboard'))
    return render_template('index.html')

@dashboard_bp.route('/dashboard')
@login_required
def view_dashboard():
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@dashboard_bp.route('/analytics')
@login_required
def view_analytics():
    user = User.query.get(session['user_id'])
    return render_template('analytics.html', user=user)

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    user_id = session['user_id']
    today = date.today()
    current_year = today.year
    current_month = today.month
    current_month_str = today.strftime('%Y-%m')

    # All-time totals
    total_income_all = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.user_id == user_id
    ).scalar()

    total_expense_all = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == user_id
    ).scalar()

    balance = float(total_income_all) - float(total_expense_all)

    # Current month totals
    monthly_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.user_id == user_id,
        extract('year', Income.date) == current_year,
        extract('month', Income.date) == current_month
    ).scalar()

    monthly_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == user_id,
        extract('year', Expense.date) == current_year,
        extract('month', Expense.date) == current_month
    ).scalar()

    expense_count = Expense.query.filter_by(user_id=user_id).count()
    income_count = Income.query.filter_by(user_id=user_id).count()
    total_transactions = expense_count + income_count

    # Current month overall budget
    overall_budget = Budget.query.filter_by(
        user_id=user_id,
        category_id=None,
        month_year=current_month_str
    ).first()
    budget_limit = float(overall_budget.amount) if overall_budget else 0.0
    budget_used_pct = round((float(monthly_expense) / budget_limit * 100), 1) if budget_limit > 0 else 0.0

    # Recent transactions (combine last 5 expenses and last 5 incomes)
    recent_expenses = Expense.query.filter_by(user_id=user_id).order_by(
        Expense.date.desc(), Expense.id.desc()
    ).limit(8).all()

    recent_incomes = Income.query.filter_by(user_id=user_id).order_by(
        Income.date.desc(), Income.id.desc()
    ).limit(8).all()

    recent_tx = []
    for exp in recent_expenses:
        recent_tx.append({
            'id': exp.id,
            'type': 'expense',
            'title': exp.description or (exp.category.name if exp.category else 'Expense'),
            'category': exp.category.name if exp.category else 'General',
            'category_color': exp.category.color if exp.category else '#ef4444',
            'category_icon': exp.category.icon if exp.category else 'shopping-cart',
            'amount': float(exp.amount),
            'date': exp.date.strftime('%Y-%m-%d'),
            'payment_method': exp.payment_method
        })

    for inc in recent_incomes:
        recent_tx.append({
            'id': inc.id,
            'type': 'income',
            'title': inc.source,
            'category': inc.category.name if inc.category else inc.source,
            'category_color': inc.category.color if inc.category else '#10b981',
            'category_icon': 'dollar-sign',
            'amount': float(inc.amount),
            'date': inc.date.strftime('%Y-%m-%d'),
            'payment_method': 'Deposit'
        })

    # Sort combined transactions descending by date
    recent_tx.sort(key=lambda x: x['date'], reverse=True)
    recent_tx = recent_tx[:8]

    # Category breakdown (Current month expenses)
    cat_breakdown_raw = db.session.query(
        Category.name,
        Category.color,
        Category.icon,
        func.sum(Expense.amount).label('total')
    ).join(Expense, Expense.category_id == Category.id).filter(
        Expense.user_id == user_id,
        extract('year', Expense.date) == current_year,
        extract('month', Expense.date) == current_month
    ).group_by(Category.name, Category.color, Category.icon).order_by(
        func.sum(Expense.amount).desc()
    ).all()

    # If current month has no data, fallback to all-time category breakdown for demonstration
    if not cat_breakdown_raw:
        cat_breakdown_raw = db.session.query(
            Category.name,
            Category.color,
            Category.icon,
            func.sum(Expense.amount).label('total')
        ).join(Expense, Expense.category_id == Category.id).filter(
            Expense.user_id == user_id
        ).group_by(Category.name, Category.color, Category.icon).order_by(
            func.sum(Expense.amount).desc()
        ).all()

    category_labels = []
    category_values = []
    category_colors = []
    for cat in cat_breakdown_raw:
        category_labels.append(cat[0])
        category_values.append(float(cat[3]))
        category_colors.append(cat[1] or '#6366f1')

    # Monthly Spending Trend (Last 6 months)
    monthly_trend = []
    for i in range(5, -1, -1):
        target_month_date = today.replace(day=1) - timedelta(days=i * 28)
        y = target_month_date.year
        m = target_month_date.month
        month_label = target_month_date.strftime('%b %Y')

        m_inc = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.user_id == user_id,
            extract('year', Income.date) == y,
            extract('month', Income.date) == m
        ).scalar()

        m_exp = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == y,
            extract('month', Expense.date) == m
        ).scalar()

        monthly_trend.append({
            'month': month_label,
            'income': float(m_inc),
            'expense': float(m_exp)
        })

    return jsonify({
        'total_income': float(total_income_all),
        'total_expenses': float(total_expense_all),
        'current_balance': balance,
        'monthly_income': float(monthly_income),
        'monthly_expenses': float(monthly_expense),
        'total_transactions': total_transactions,
        'budget_limit': budget_limit,
        'budget_used_pct': budget_used_pct,
        'recent_transactions': recent_tx,
        'category_breakdown': {
            'labels': category_labels,
            'values': category_values,
            'colors': category_colors
        },
        'monthly_trend': monthly_trend
    })
