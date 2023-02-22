from config.db import db
from datetime import datetime
from helpers.constants import Constants


class PhoneNumber(db.Model):
    __tablename__ = 'phone_numbers'
    __table_args__ = (
        db.UniqueConstraint('number', 'deleted_at', name='unique__number__deleted_at'),
        db.UniqueConstraint('twilio_sid', 'deleted_at', name='unique__twilio_sid__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    subaccount_id = db.Column(db.Integer, db.ForeignKey('subaccounts.id'), nullable = False)
    subaccount = db.relationship('SubAccount', foreign_keys = [subaccount_id])
    number = db.Column(db.String(20), nullable = False)
    twilio_sid = db.Column(db.String(50), nullable=False)
    emergency_addr_id = db.Column(db.Integer, db.ForeignKey('emergency_addresses.id'))
    emergency_addr = db.relationship('EmergencyAddress', foreign_keys = [emergency_addr_id])
    status = db.Column(db.Integer, nullable = False, default = 1)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['subaccount_id'] = self.subaccount_id
        response['subaccount'] = self.subaccount.as_dict()
        response['number'] = self.number
        response['identity'] = self.number.replace('+','')
        response['twilio_sid'] = self.twilio_sid
        response['emergency_addr_id'] = self.emergency_addr_id
        response['status'] = self.status
        return response

    def save(self):
        db.session.add(self)
        db.session.commit()
        
class CallForwardingRule(db.Model):
    __tablename__ = 'call_forwarding_rules'
    __table_args__ = (
        db.UniqueConstraint('phone_number_id', 'number', 'deleted_at', name='unique__phone_number_id__number__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_numbers.id'), nullable = False)
    phone_number = db.relationship('PhoneNumber', foreign_keys = [phone_number_id])
    number = db.Column(db.String(50), nullable=False)
    number_type = db.Column(db.Enum(Constants.PhoneNumberTypes), nullable = False)
    duration = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable = False, default = 1)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['number'] = self.number
        response['number_type'] = self.number_type.name
        response['duration'] = self.duration
        response['status'] = self.status
        return response

    def save(self):
        db.session.add(self)
        db.session.commit()