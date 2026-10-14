from datetime import datetime
from . import db

class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    month_year = db.Column(db.String(7), nullable=False, index=True)  # Format 'YYYY-MM'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category_id', 'month_year', name='uq_user_cat_month'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Total Monthly Budget',
            'category_color': self.category.color if self.category else '#6366f1',
            'category_icon': self.category.icon if self.category else 'pie-chart',
            'amount': float(self.amount),
            'month_year': self.month_year,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Budget {self.id} - ${self.amount} ({self.month_year})>"
