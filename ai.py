import math
from datetime import date, timedelta
from flask import Blueprint, session, jsonify, current_app
from sqlalchemy import func, extract
from models import db, Expense, Income, Category, Budget, User
from . import login_required

ai_bp = Blueprint('ai', __name__)

def generate_heuristic_insights(user, monthly_expense, monthly_income, cat_totals, expenses_list):
    """
    Advanced statistical financial intelligence engine.
    Analyzes spending habits, detects anomalies, evaluates 50/30/20 rule,
    and returns rich actionable insights.
    """
    insights = []
    anomalies = []
    saving_tips = []
    budget_recommendations = []

    # 1. Monthly Summary & Cash Flow Rate
    net_savings = monthly_income - monthly_expense
    savings_rate = (net_savings / monthly_income * 100) if monthly_income > 0 else 0

    if monthly_income == 0 and monthly_expense == 0:
        return {
            'monthly_summary': 'No transaction activity recorded for this month yet. Start logging your income and expenses to unlock AI financial intelligence!',
            'highest_spending_category': None,
            'unusual_spending': [],
            'saving_suggestions': ['Add your recurring income and regular expenses to receive tailored savings advice.'],
            'budget_recommendations': ['Set an overall monthly target to ensure you save at least 20% of your earnings.'],
            'financial_health_score': 70,
            'insights': ['Awaiting financial records to begin continuous spending analysis.']
        }

    # Financial Health Score (0 - 100)
    health_score = 70
    if monthly_income > 0:
        if savings_rate >= 25:
            health_score = min(100, health_score + 25)
            insights.append(f"Outstanding savings rate of {savings_rate:.1f}% this month! You are significantly ahead of the average 20% financial benchmark.")
        elif savings_rate >= 10:
            health_score = min(100, health_score + 10)
            insights.append(f"Healthy savings rate of {savings_rate:.1f}%. Aim to increase your allocation toward investments or high-yield savings.")
        elif savings_rate >= 0:
            health_score = max(40, health_score - 15)
            insights.append(f"Narrow surplus: You're spending {100 - savings_rate:.1f}% of your earnings. Build a 1-month safety buffer.")
        else:
            health_score = max(20, health_score - 40)
            insights.append(f"Deficit Alert: Your expenses (${monthly_expense:,.2f}) exceed your income (${monthly_income:,.2f}) by ${abs(net_savings):,.2f}.")

    # 2. Category with Highest Spending
    highest_cat = None
    if cat_totals:
        top_cat = cat_totals[0]
        cat_pct = (top_cat['total'] / monthly_expense * 100) if monthly_expense > 0 else 0
        highest_cat = {
            'name': top_cat['name'],
            'amount': top_cat['total'],
            'percentage': round(cat_pct, 1)
        }

        if cat_pct > 40:
            insights.append(f"High Category Concentration: '{top_cat['name']}' represents {cat_pct:.1f}% of all your monthly expenditures. Diversifying or capping this area will quickly free up capital.")
            saving_tips.append(f"Audit '{top_cat['name']}': Setting a weekly cap on this single category can save you up to ${top_cat['total'] * 0.15:,.2f} per month.")

    # 3. Unusual Spending Detection (Anomaly Detection using Mean + Std Dev)
    amounts = [float(exp.amount) for exp in expenses_list]
    if len(amounts) >= 3:
        avg_amt = sum(amounts) / len(amounts)
        variance = sum((x - avg_amt) ** 2 for x in amounts) / len(amounts)
        std_dev = math.sqrt(variance)
        threshold = avg_amt + (1.75 * std_dev)

        for exp in expenses_list:
            exp_amt = float(exp.amount)
            if exp_amt > threshold and exp_amt > 100:
                anomalies.append({
                    'id': exp.id,
                    'description': exp.description or (exp.category.name if exp.category else 'Expense'),
                    'amount': exp_amt,
                    'date': exp.date.strftime('%Y-%m-%d') if hasattr(exp.date, 'strftime') else str(exp.date),
                    'category': exp.category.name if exp.category else 'General',
                    'reason': f"Transaction amount (${exp_amt:,.2f}) is substantially higher than your typical average (${avg_amt:,.2f})."
                })

    # 4. Personalized Saving Suggestions
    if highest_cat and highest_cat['percentage'] > 25:
        saving_tips.append(f"Apply the 48-Hour Rule for discretionary purchases in {highest_cat['name']}. Delaying impulsive purchases reduces regret spending by ~30%.")

    if monthly_income > 0:
        recommended_savings = monthly_income * 0.20
        saving_tips.append(f"Automate pay-yourself-first: Transfer ${recommended_savings:,.2f} (20% of income) into a separate emergency fund on payday.")
    else:
        saving_tips.append("Review recurring digital subscriptions (streaming, gym, apps) to identify unused memberships.")

    # 5. Budget Recommendations (50/30/20 benchmark)
    if monthly_income > 0:
        needs_target = monthly_income * 0.50
        wants_target = monthly_income * 0.30
        savings_target = monthly_income * 0.20
        budget_recommendations.append(f"Ideal Monthly Needs budget: ${needs_target:,.2f} (Rent, Utilities, Food, Transit).")
        budget_recommendations.append(f"Ideal Monthly Wants budget: ${wants_target:,.2f} (Shopping, Dining out, Entertainment).")
        budget_recommendations.append(f"Target Monthly Savings & Investments: ${savings_target:,.2f}.")
    else:
        budget_recommendations.append(f"Based on current expense velocity (${monthly_expense:,.2f}), set a monthly limit of ${monthly_expense * 0.9:,.2f} to build a 10% cash surplus.")

    # Monthly Summary text
    summary_text = (
        f"In this billing cycle, you have generated ${monthly_income:,.2f} in earnings and logged ${monthly_expense:,.2f} in expenditures, "
        f"resulting in a net cash flow of ${net_savings:,.2f}. "
    )
    if highest_cat:
        summary_text += f"Your dominant expenditure category is {highest_cat['name']} at ${highest_cat['amount']:,.2f} ({highest_cat['percentage']}% of total expenses)."

    return {
        'monthly_summary': summary_text,
        'highest_spending_category': highest_cat,
        'unusual_spending': anomalies[:4], # Top 4 anomalies
        'saving_suggestions': saving_tips,
        'budget_recommendations': budget_recommendations,
        'financial_health_score': int(health_score),
        'insights': insights
    }

@ai_bp.route('/api/ai-insights', methods=['GET'])
@login_required
def get_ai_insights():
    user_id = session['user_id']
    user = User.query.get(user_id)
    today = date.today()
    current_year = today.year
    current_month = today.month

    # Current month income & expenses
    monthly_income = float(db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.user_id == user_id,
        extract('year', Income.date) == current_year,
        extract('month', Income.date) == current_month
    ).scalar())

    monthly_expense = float(db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == user_id,
        extract('year', Expense.date) == current_year,
        extract('month', Expense.date) == current_month
    ).scalar())

    # Fallback to all-time if current month is brand new
    if monthly_expense == 0 and monthly_income == 0:
        monthly_income = float(db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
            Income.user_id == user_id
        ).scalar())
        monthly_expense = float(db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == user_id
        ).scalar())

    # Category breakdown
    cat_query = db.session.query(
        Category.name,
        func.sum(Expense.amount).label('total')
    ).join(Expense, Expense.category_id == Category.id).filter(
        Expense.user_id == user_id
    ).group_by(Category.name).order_by(func.sum(Expense.amount).desc()).all()

    cat_totals = [{'name': name, 'total': float(total)} for name, total in cat_query]

    # Recent expenses list for anomaly detection
    recent_expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).limit(50).all()

    # Generate insights using modular engine
    insights_payload = generate_heuristic_insights(
        user=user,
        monthly_expense=monthly_expense,
        monthly_income=monthly_income,
        cat_totals=cat_totals,
        expenses_list=recent_expenses
    )

    return jsonify({
        'success': True,
        'provider': current_app.config.get('AI_PROVIDER', 'heuristic'),
        'data': insights_payload
    })
