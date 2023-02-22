from config.db import db
from datetime import datetime


class EmergencyAddress(db.Model):
    __tablename__ = 'emergency_addresses'
    __table_args__ = (
        db.UniqueConstraint('twilio_sid', 'deleted_at', name='unique__twilio_sid__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    subaccount_id = db.Column(db.Integer, db.ForeignKey('subaccounts.id'), nullable = False)
    subaccount = db.relationship('SubAccount', foreign_keys = [subaccount_id])
    twilio_sid = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(50), nullable=False)
    street = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(50), nullable=False)
    iso_country = db.Column(db.String(10), nullable=False)
    emergency_enabled = db.Column(db.Boolean, nullable=False, default=False)
    validated = db.Column(db.Boolean, nullable=False, default=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.Integer, nullable = False, default = 1)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['subaccount_id'] = self.subaccount_id
        response['twilio_sid'] = self.twilio_sid
        response['street'] = self.street
        response['city'] = self.city
        response['region'] = self.region
        response['postal_code'] = self.postal_code
        response['iso_country'] = self.iso_country
        response['emergency_enabled'] = self.emergency_enabled
        response['validated'] = self.validated
        response['verified'] = self.verified
        response['status'] = self.status
        return response
    
    def save(self):
        db.session.add(self)
        db.session.commit()