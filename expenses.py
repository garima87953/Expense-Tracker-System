import csv
import io
from datetime import datetime, date
from flask import Blueprint, render_template, request, session, jsonify, Response
from models import db, User, Expense, Category
from . import login_required

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/expenses')
@login_required
def view_expenses():
    user = User.query.get(session['user_id'])
    categories = Category.query.filter(
        (Category.user_id == None) | (Category.user_id == user.id),
        Category.type == 'expense'
    ).order_by(Category.name.asc()).all()
    return render_template('expenses.html', user=user, categories=categories)

@expenses_bp.route('/api/expenses', methods=['GET'])
@login_required
def get_expenses():
    user_id = session['user_id']
    query = Expense.query.filter_by(user_id=user_id)

    # Search query
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(Expense.description.ilike(f'%{search}%'))

    # Category filter
    category_id = request.args.get('category_id')
    if category_id and category_id.isdigit():
        query = query.filter(Expense.category_id == int(category_id))

    # Date range filters
    start_date = request.args.get('start_date')
    if start_date:
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date >= s_date)
        except ValueError:
            pass

    end_date = request.args.get('end_date')
    if end_date:
        try:
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date <= e_date)
        except ValueError:
            pass

    # Sorting
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'date_asc':
        query = query.order_by(Expense.date.asc(), Expense.id.asc())
    elif sort_by == 'amount_desc':
        query = query.order_by(Expense.amount.desc())
    elif sort_by == 'amount_asc':
        query = query.order_by(Expense.amount.asc())
    else:  # default date_desc
        query = query.order_by(Expense.date.desc(), Expense.id.desc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'expenses': [exp.to_dict() for exp in paginated.items],
        'total': paginated.total,
        'page': paginated.page,
        'pages': paginated.pages,
        'per_page': paginated.per_page
    })

@expenses_bp.route('/api/expenses', methods=['POST'])
@login_required
def create_expense():
    user_id = session['user_id']
    data = request.get_json() or {}

    amount = data.get('amount')
    category_id = data.get('category_id')
    description = data.get('description', '').strip()
    date_str = data.get('date')
    payment_method = data.get('payment_method', 'Credit Card')

    if not amount or float(amount) <= 0:
        return jsonify({'error': 'Amount must be greater than 0.'}), 400
    if not category_id:
        return jsonify({'error': 'Please select a valid category.'}), 400

    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': 'Category does not exist.'}), 404

    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    expense = Expense(
        user_id=user_id,
        category_id=int(category_id),
        amount=round(float(amount), 2),
        description=description,
        date=parsed_date,
        payment_method=payment_method
    )
    db.session.add(expense)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Expense created successfully!', 'expense': expense.to_dict()}), 201

@expenses_bp.route('/api/expenses/<int:expense_id>', methods=['GET'])
@login_required
def get_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=session['user_id']).first()
    if not expense:
        return jsonify({'error': 'Expense not found.'}), 404
    return jsonify(expense.to_dict())

@expenses_bp.route('/api/expenses/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=session['user_id']).first()
    if not expense:
        return jsonify({'error': 'Expense not found.'}), 404

    data = request.get_json() or {}
    if 'amount' in data:
        if float(data['amount']) <= 0:
            return jsonify({'error': 'Amount must be greater than 0.'}), 400
        expense.amount = round(float(data['amount']), 2)

    if 'category_id' in data:
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Category does not exist.'}), 404
        expense.category_id = int(data['category_id'])

    if 'description' in data:
        expense.description = data['description'].strip()

    if 'payment_method' in data:
        expense.payment_method = data['payment_method']

    if 'date' in data and data['date']:
        try:
            expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    db.session.commit()
    return jsonify({'success': True, 'message': 'Expense updated successfully!', 'expense': expense.to_dict()})

@expenses_bp.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=session['user_id']).first()
    if not expense:
        return jsonify({'error': 'Expense not found.'}), 404

    db.session.delete(expense)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Expense deleted successfully!'})

@expenses_bp.route('/api/expenses/export', methods=['GET'])
@login_required
def export_expenses_csv():
    user_id = session['user_id']
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Category', 'Description', 'Amount', 'Payment Method'])

    for exp in expenses:
        writer.writerow([
            exp.id,
            exp.date.strftime('%Y-%m-%d'),
            exp.category.name if exp.category else 'N/A',
            exp.description or '',
            f"{float(exp.amount):.2f}",
            exp.payment_method or ''
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=expenses_{date.today().strftime("%Y%m%d")}.csv'}
    )
