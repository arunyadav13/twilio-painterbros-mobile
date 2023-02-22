from config.db import db
from datetime import datetime
from helpers.constants import Constants


class Contact(db.Model):
    __tablename__ = 'contacts'
    __table_args__ = (
        db.UniqueConstraint('number', 'tenant_id', 'deleted_at', name='unique__number__tenant_id__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    tenant_id = db.Column(db.String(100), db.ForeignKey('subaccounts.tenant_id'), nullable = False)
    tenant = db.relationship('SubAccount', foreign_keys = [tenant_id])
    number = db.Column(db.String(20), nullable = False)
    name = db.Column(db.String(255))
    type = db.Column(db.String(25))
    sms_consent = db.Column(db.Boolean, default=True)
    status = db.Column(db.Integer, nullable = False, default = 1)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['tenant_id'] = self.tenant_id
        response['number'] = self.number
        response['name'] = self.name if self.name else self.number
        response['type'] = self.type
        response['sms_consent'] = self.sms_consent
        response['status'] = self.status
        return response

    def save(self):
        db.session.add(self)
        db.session.commit()