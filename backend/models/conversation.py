from config.db import db
from datetime import datetime
from helpers.constants import Constants

class Conversation(db.Model):
    __tablename__ = 'conversations'
    __table_args__ = (
        db.UniqueConstraint('twilio_sid', 'deleted_at', name='unique__twilio_sid__deleted_at'),
        db.UniqueConstraint('unique_name', 'deleted_at', name='unique__unique_name__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    subaccount_id = db.Column(db.Integer, db.ForeignKey('subaccounts.id'), nullable = False)
    subaccount = db.relationship('SubAccount', foreign_keys = [subaccount_id])
    twilio_sid = db.Column(db.String(50), nullable=False)
    unique_name = db.Column(db.String(50), nullable=False)
    participants = db.relationship('ConversationParticipant')
    messages = db.relationship('ConversationMessage')
    status = db.Column(db.Enum(Constants.Status), nullable=False, default=Constants.Status.ACTIVE)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['twilio_sid'] = self.twilio_sid
        response['unique_name'] = self.unique_name

        response['participants'] = list()
        for participant in self.participants:
            response['participants'].append(participant.as_dict())

        response['messages'] = list()
        response['last_message'] = dict()
        for message in self.messages:
            message = message.as_dict()
            response['messages'].append(message)
            response['last_message'] = message

        response['status'] = self.status.name
        return response

    def save(self):
        db.session.add(self)
        db.session.commit()

class ConversationParticipant(db.Model):
    __tablename__ = 'conversation_participants'
    __table_args__ = (
        db.UniqueConstraint('twilio_sid', 'deleted_at', name='unique__twilio_sid__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    twilio_sid = db.Column(db.String(50), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable = False)
    conversation = db.relationship('Conversation', foreign_keys = [conversation_id])
    type = db.Column(db.String(50))
    identity = db.Column(db.String(50))
    proxy_address = db.Column(db.String(50))
    address = db.Column(db.String(50))
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable = False)
    contact = db.relationship('Contact', foreign_keys = [contact_id])
    status = db.Column(db.Enum(Constants.Status), nullable=False, default=Constants.Status.ACTIVE)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['twilio_sid'] = self.twilio_sid
        response['type'] = self.type
        response['identity'] = self.identity
        response['proxy_address'] = self.proxy_address
        response['address'] = self.address
        response['contact'] = self.contact.as_dict()
        response['status'] = self.status.name
        return response

    def save(self):
        db.session.add(self)
        db.session.commit()

class ConversationMessage(db.Model):
    __tablename__ = 'conversation_messages'
    __table_args__ = (
        db.UniqueConstraint('twilio_sid', 'deleted_at', name='unique__twilio_sid__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable = False)
    conversation = db.relationship('Conversation', foreign_keys = [conversation_id])
    participant_id = db.Column(db.Integer, db.ForeignKey('conversation_participants.id'), nullable = False)
    participant = db.relationship('ConversationParticipant', foreign_keys = [participant_id])
    twilio_sid = db.Column(db.String(50), nullable=False)
    body = db.Column(db.Text, nullable=False)
    media = db.Column(db.Text)
    delivery  = db.Column(db.JSON)
    delivery_receipts  = db.Column(db.JSON)
    status = db.Column(db.Enum(Constants.Status), nullable=False, default=Constants.Status.ACTIVE)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['conversation_sid'] = self.conversation.twilio_sid
        response['participant'] = self.participant.as_dict()
        response['twilio_sid'] = self.twilio_sid
        response['body'] = self.body
        response['media'] = self.media
        response['delivery'] = self.delivery if self.delivery else {'sent':'none','delivered':'none','read':'none','failed':'none','undelivered':'none'}
        response['delivery_receipts'] = self.delivery_receipts
        response['status'] = self.status.name
        response['created_at'] = str(self.created_at)
        return response

    def save(self):
        db.session.add(self)
        db.session.commit()