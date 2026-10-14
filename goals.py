from datetime import datetime, date
from flask import Blueprint, render_template, request, session, jsonify
from models import db, User, Goal
from . import login_required

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('/goals')
@login_required
def view_goals():
    user = User.query.get(session['user_id'])
    return render_template('goals.html', user=user)

@goals_bp.route('/api/goals', methods=['GET'])
@login_required
def get_goals():
    user_id = session['user_id']
    goals = Goal.query.filter_by(user_id=user_id).order_by(Goal.created_at.desc()).all()
    
    total_target = sum(float(g.target_amount) for g in goals)
    total_saved = sum(float(g.saved_amount) for g in goals)
    completed_count = sum(1 for g in goals if float(g.saved_amount) >= float(g.target_amount))

    return jsonify({
        'goals': [g.to_dict() for g in goals],
        'total_target': total_target,
        'total_saved': total_saved,
        'completed_count': completed_count,
        'total_goals': len(goals)
    })

@goals_bp.route('/api/goals', methods=['POST'])
@login_required
def create_goal():
    user_id = session['user_id']
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    target_amount = data.get('target_amount')
    initial_saved = data.get('saved_amount', 0.0)
    target_date_str = data.get('target_date')
    icon = data.get('icon', '🐷').strip()
    color = data.get('color', '#ec4899').strip()

    if not name:
        return jsonify({'error': 'Goal name is required (e.g. Dream Vacation 🌸).'}), 400
    if not target_amount or float(target_amount) <= 0:
        return jsonify({'error': 'Target amount must be greater than 0.'}), 400

    parsed_date = None
    if target_date_str:
        try:
            parsed_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    goal = Goal(
        user_id=user_id,
        name=name,
        target_amount=round(float(target_amount), 2),
        saved_amount=max(0.0, round(float(initial_saved or 0), 2)),
        target_date=parsed_date,
        icon=icon or '🐷',
        color=color or '#ec4899'
    )
    db.session.add(goal)
    db.session.commit()

    return jsonify({'success': True, 'message': 'New savings goal created! 🌸', 'goal': goal.to_dict()}), 201

@goals_bp.route('/api/goals/<int:goal_id>/deposit', methods=['POST'])
@login_required
def deposit_to_goal(goal_id):
    user_id = session['user_id']
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()

    if not goal:
        return jsonify({'error': 'Savings goal not found.'}), 404

    data = request.get_json() or {}
    amount = data.get('amount')

    if not amount or float(amount) <= 0:
        return jsonify({'error': 'Deposit amount must be greater than 0.'}), 400

    goal.saved_amount = float(goal.saved_amount) + float(amount)
    db.session.commit()

    is_celebration = float(goal.saved_amount) >= float(goal.target_amount)

    return jsonify({
        'success': True,
        'message': f"Added ${float(amount):,.2f} to {goal.name}! {'🎉 Goal unlocked! Super superstar!' if is_celebration else 'Piggy is happy! 🐷'}",
        'is_completed': is_celebration,
        'goal': goal.to_dict()
    })

@goals_bp.route('/api/goals/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    user_id = session['user_id']
    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()

    if not goal:
        return jsonify({'error': 'Savings goal not found.'}), 404

    db.session.delete(goal)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Savings goal removed.'})
