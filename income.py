from datetime import datetime, date
from flask import Blueprint, render_template, request, session, jsonify
from models import db, User, Income, Category
from . import login_required

income_bp = Blueprint('income', __name__)

@income_bp.route('/income')
@login_required
def view_income():
    user = User.query.get(session['user_id'])
    income_categories = Category.query.filter(
        (Category.user_id == None) | (Category.user_id == user.id),
        Category.type == 'income'
    ).order_by(Category.name.asc()).all()
    return render_template('income.html', user=user, categories=income_categories)

@income_bp.route('/api/income', methods=['GET'])
@login_required
def get_income():
    user_id = session['user_id']
    query = Income.query.filter_by(user_id=user_id)

    search = request.args.get('search', '').strip()
    if search:
        query = query.filter((Income.source.ilike(f'%{search}%')) | (Income.description.ilike(f'%{search}%')))

    start_date = request.args.get('start_date')
    if start_date:
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Income.date >= s_date)
        except ValueError:
            pass

    end_date = request.args.get('end_date')
    if end_date:
        try:
            e_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Income.date <= e_date)
        except ValueError:
            pass

    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'amount_desc':
        query = query.order_by(Income.amount.desc())
    elif sort_by == 'amount_asc':
        query = query.order_by(Income.amount.asc())
    elif sort_by == 'date_asc':
        query = query.order_by(Income.date.asc(), Income.id.asc())
    else:
        query = query.order_by(Income.date.desc(), Income.id.desc())

    incomes = query.all()
    total_income = sum(float(i.amount) for i in incomes)

    return jsonify({
        'incomes': [inc.to_dict() for inc in incomes],
        'total_amount': total_income
    })

@income_bp.route('/api/income', methods=['POST'])
@login_required
def create_income():
    user_id = session['user_id']
    data = request.get_json() or {}

    amount = data.get('amount')
    source = data.get('source', '').strip()
    description = data.get('description', '').strip()
    category_id = data.get('category_id')
    date_str = data.get('date')

    if not amount or float(amount) <= 0:
        return jsonify({'error': 'Amount must be greater than 0.'}), 400
    if not source:
        return jsonify({'error': 'Source is required (e.g., Salary, Freelance).'}), 400

    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    inc = Income(
        user_id=user_id,
        category_id=int(category_id) if category_id else None,
        amount=round(float(amount), 2),
        source=source,
        description=description,
        date=parsed_date
    )
    db.session.add(inc)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Income added successfully!', 'income': inc.to_dict()}), 201

@income_bp.route('/api/income/<int:income_id>', methods=['GET'])
@login_required
def get_single_income(income_id):
    inc = Income.query.filter_by(id=income_id, user_id=session['user_id']).first()
    if not inc:
        return jsonify({'error': 'Income record not found.'}), 404
    return jsonify(inc.to_dict())

@income_bp.route('/api/income/<int:income_id>', methods=['PUT'])
@login_required
def update_income(income_id):
    inc = Income.query.filter_by(id=income_id, user_id=session['user_id']).first()
    if not inc:
        return jsonify({'error': 'Income record not found.'}), 404

    data = request.get_json() or {}
    if 'amount' in data:
        if float(data['amount']) <= 0:
            return jsonify({'error': 'Amount must be greater than 0.'}), 400
        inc.amount = round(float(data['amount']), 2)

    if 'source' in data:
        inc.source = data['source'].strip()

    if 'category_id' in data:
        inc.category_id = int(data['category_id']) if data['category_id'] else None

    if 'description' in data:
        inc.description = data['description'].strip()

    if 'date' in data and data['date']:
        try:
            inc.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    db.session.commit()
    return jsonify({'success': True, 'message': 'Income updated successfully!', 'income': inc.to_dict()})

@income_bp.route('/api/income/<int:income_id>', methods=['DELETE'])
@login_required
def delete_income(income_id):
    inc = Income.query.filter_by(id=income_id, user_id=session['user_id']).first()
    if not inc:
        return jsonify({'error': 'Income record not found.'}), 404

    db.session.delete(inc)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Income deleted successfully!'})
