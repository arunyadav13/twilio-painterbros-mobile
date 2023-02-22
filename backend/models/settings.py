from config.db import db
from datetime import datetime


class AccountSettings(db.Model):
    __tablename__ = 'account_settings'
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'name', 'deleted_at', name='unique__tenant_id__name__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    tenant_id = db.Column(db.String(100), db.ForeignKey('subaccounts.tenant_id'), nullable = False)
    tenant = db.relationship('SubAccount', foreign_keys = [tenant_id])
    name = db.Column(db.String(255), nullable = False)
    value = db.Column(db.Text, nullable = False)
    status = db.Column(db.Integer, nullable = False, default = 1)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['name'] = self.name
        response['value'] = self.value
        response['status'] = self.status
        return response

    def save(self):
        db.session.add(self)
        db.session.commit()

class SubaccountSettings(db.Model):
    __tablename__ = 'subaccount_settings'
    __table_args__ = (
        db.UniqueConstraint('subaccount_id', 'name', 'deleted_at', name='unique__subaccount_id__name__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    subaccount_id = db.Column(db.Integer, db.ForeignKey('subaccounts.id'), nullable = False)
    subaccount = db.relationship('SubAccount', foreign_keys = [subaccount_id])
    name = db.Column(db.String(255), nullable = False)
    value = db.Column(db.Text, nullable = False)
    status = db.Column(db.Integer, nullable = False, default = 1)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['name'] = self.name
        response['value'] = self.value
        response['status'] = self.status
        return response

    def save(self):
        db.session.add(self)
        db.session.commit()