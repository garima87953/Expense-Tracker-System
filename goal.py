from datetime import datetime, date
from . import db

class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    saved_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    target_date = db.Column(db.Date, nullable=True)
    icon = db.Column(db.String(50), nullable=False, default='🐷')
    color = db.Column(db.String(20), nullable=False, default='#ec4899')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        target = float(self.target_amount)
        saved = float(self.saved_amount)
        pct = round((saved / target * 100), 1) if target > 0 else 0.0
        remaining = max(0.0, target - saved)
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'target_amount': target,
            'saved_amount': saved,
            'remaining_amount': round(remaining, 2),
            'percentage': min(100.0, pct),
            'is_completed': saved >= target,
            'target_date': self.target_date.strftime('%Y-%m-%d') if self.target_date else None,
            'icon': self.icon or '🐷',
            'color': self.color or '#ec4899',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Goal {self.name} (${self.saved_amount}/${self.target_amount})>"
