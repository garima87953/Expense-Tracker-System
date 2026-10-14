from datetime import datetime
from . import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='expense')  # 'expense' or 'income'
    icon = db.Column(db.String(50), nullable=False, default='tag')
    color = db.Column(db.String(20), nullable=False, default='#6366f1')
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    expenses = db.relationship('Expense', backref='category', lazy=True)
    incomes = db.relationship('Income', backref='category', lazy=True)
    budgets = db.relationship('Budget', backref='category', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'icon': self.icon,
            'color': self.color,
            'is_default': self.is_default
        }

    def __repr__(self):
        return f"<Category {self.name} ({self.type})>"
