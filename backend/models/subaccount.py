from config.db import db
from datetime import datetime


class SubAccount(db.Model):
    __tablename__ = 'subaccounts'
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'subtenant_id', 'deleted_at', name='unique__tenant_id_subtenant_id__deleted_at'),
        db.UniqueConstraint('account_sid', 'deleted_at', name='unique__account_sid__deleted_at'),
    )

    id = db.Column(db.Integer, primary_key = True)
    tenant_id = db.Column(db.String(100), nullable = False)
    subtenant_id = db.Column(db.String(100), nullable = False)
    account_sid = db.Column(db.String(50), nullable=False)
    auth_token = db.Column(db.String(50), nullable=False)
    account_status = db.Column(db.String(20), nullable=False)
    api_key = db.Column(db.String(50))
    api_secret = db.Column(db.String(50))
    twiml_app_sid = db.Column(db.String(50))
    sync_service_sid = db.Column(db.String(50))
    call_logs_sync_service_sid = db.Column(db.String(50))
    conversation_service_sid = db.Column(db.String(50))
    messaging_service_sid = db.Column(db.String(50))
    a2p_10dlc_campaign_sid = db.Column(db.String(50))
    ivr_flow_sid = db.Column(db.String(50))
    status = db.Column(db.Integer, nullable = False, default = 1)
    created_at = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=False, default=datetime.fromisoformat('0001-01-01T00:00:00.000000'))

    def as_dict(self):
        response = dict()
        response['id'] = self.id
        response['tenant_id'] = self.tenant_id
        response['subtenant_id'] = self.subtenant_id
        response['account_sid'] = self.account_sid
        response['auth_token'] = self.auth_token
        response['account_status'] = self.account_status
        response['api_key'] = self.api_key
        response['api_secret'] = self.api_secret
        response['twiml_app_sid'] = self.twiml_app_sid
        response['sync_service_sid'] = self.sync_service_sid
        response['call_logs_sync_service_sid'] = self.call_logs_sync_service_sid
        response['conversation_service_sid'] = self.conversation_service_sid
        response['messaging_service_sid'] = self.messaging_service_sid
        response['a2p_10dlc_campaign_sid'] = self.a2p_10dlc_campaign_sid
        response['ivr_flow_sid'] = self.ivr_flow_sid
        response['status'] = self.status
        return response

    def save(self):
        db.session.add(self)
        db.session.commit()