from config.db import db
from helpers.constants import Constants
from datetime import datetime


class CallLog(db.Model):
    __tablename__ = 'call_logs'
    __table_args__ = (
        db.UniqueConstraint('call_sid', 'conference_sid', 'deleted_at', name='unique__call_sid__conference_sid__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    subaccount_id = db.Column(db.Integer, db.ForeignKey('subaccounts.id'), nullable = False)
    subaccount = db.relationship('SubAccount', foreign_keys = [subaccount_id])
    call_sid = db.Column(db.String(50), nullable=False)
    source_call_sid = db.Column(db.String(50), nullable=True)
    conference_sid = db.Column(db.String(50), nullable=False)
    source_number = db.Column(db.String(50), nullable=False)
    source_name = db.Column(db.String(50))
    source_phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_numbers.id'))
    source_user_id = db.Column(db.String(100))
    destination_number = db.Column(db.String(50), nullable=False)
    destination_name = db.Column(db.String(50))
    destination_phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_numbers.id'))
    destination_user_id = db.Column(db.String(100))
    log_for_user_id = db.Column(db.String(100), nullable=False)
    call_status = db.Column(db.String(20), nullable=False)
    direction = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    meta_data  = db.Column(db.JSON)
    call_duration = db.Column(db.Integer)
    status = db.Column(db.Enum(Constants.Status), nullable=False, default=Constants.Status.ACTIVE)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))
    
    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['subaccount_id'] = self.subaccount_id
        response['subaccount'] = self.subaccount.as_dict()
        response['call_sid'] = self.call_sid
        response['source_call_sid'] = self.source_call_sid
        response['conference_sid'] = self.conference_sid
        response['source_number'] = self.source_number
        response['source_name'] = self.source_name
        response['source_phone_number_id'] = self.source_phone_number_id
        response['source_user_id'] = self.source_user_id
        response['destination_number'] = self.destination_number
        response['destination_name'] = self.destination_name
        response['destination_phone_number_id'] = self.destination_phone_number_id
        response['destination_user_id'] = self.destination_user_id
        response['log_for_user_id'] = self.log_for_user_id
        response['call_status'] = self.call_status
        response['direction'] = self.direction
        response['timestamp'] = self.timestamp
        response['call_duration'] = self.call_duration
        return response
    
    def save(self):
        db.session.add(self)
        db.session.commit()

class Voicemail(db.Model):
    __tablename__ = 'voicemails'

    id = db.Column(db.Integer, primary_key = True)
    call_log_id = db.Column(db.Integer, db.ForeignKey('call_logs.id'))
    call_log = db.relationship('CallLog', foreign_keys = [call_log_id])
    twilio_sid = db.Column(db.String(50), unique=True, nullable=False)
    call_sid = db.Column(db.String(50), unique=True, nullable=False)
    recording_start_at = db.Column(db.DateTime)
    duration = db.Column(db.Integer, nullable=False, default=0)
    transcribed_text = db.Column(db.Text)
    recording_status = db.Column(db.String(50))
    s3_path = db.Column(db.String(200))
    phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_numbers.id'))
    status = db.Column(db.Enum(Constants.Status), nullable=False, default=Constants.Status.ACTIVE)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))
    
    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['call_log'] = self.call_log.as_dict() if self.call_log_id else None
        response['s3_path'] = self.s3_path
        return response
    
    def save(self):
        db.session.add(self)
        db.session.commit()