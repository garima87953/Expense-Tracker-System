from datetime import datetime, date
from . import db

class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255), default='')
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    payment_method = db.Column(db.String(50), nullable=False, default='Credit Card')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Unknown',
            'category_icon': self.category.icon if self.category else 'tag',
            'category_color': self.category.color if self.category else '#6366f1',
            'amount': float(self.amount),
            'description': self.description or '',
            'date': self.date.strftime('%Y-%m-%d') if self.date else '',
            'payment_method': self.payment_method or 'Cash',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Expense {self.id} - ${self.amount} ({self.date})>"
