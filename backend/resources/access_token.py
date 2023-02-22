import uuid
from flask_restful import Resource
from flask import jsonify, request
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant, SyncGrant, ChatGrant
from helpers.app_helper import AppHelper
from helpers.twilio_helper import TwilioHelper
from models.subaccount import SubAccount

class AccessTokenApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        phone_number = input.get('number', None)

        if not tenant_id or not subtenant_id or not phone_number:
            return {'message': 'Missing required parameters'}, 400

        subaccount = SubAccount.query.filter(SubAccount.status==1, SubAccount.tenant_id==tenant_id, SubAccount.subtenant_id==subtenant_id).first()
        if not subaccount:
            return {'message': 'Subaccount does not exist'}, 400

        if not subaccount.api_key or not subaccount.api_secret or not subaccount.twiml_app_sid or not subaccount.sync_service_sid or not subaccount.conversation_service_sid:
            return {'message': 'Subaccount is not configured properly, please contact administrator'}, 400

        user_identity = AppHelper().get_user_identity(phone_number)
        if not user_identity:
            return {'message': 'Invalid user identity.'}, 400

        try:
            client = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id}).get_twilio_client()
            client.sync.v1 \
                .services(subaccount.sync_service_sid) \
                .sync_lists \
                .create(unique_name=user_identity)
        except Exception as e:
            pass

        device_id = str(uuid.uuid4())
        access_token_ttl = 86400
        access_token = AccessToken(
            subaccount.account_sid,
            subaccount.api_key,
            subaccount.api_secret,
            identity=user_identity,
            ttl=access_token_ttl
        )

        sync_access_token = AccessToken(
            subaccount.account_sid,
            subaccount.api_key,
            subaccount.api_secret,
            identity=f'{user_identity}:{device_id}',
            ttl=access_token_ttl
        )
        
        call_log_sync_access_token = AccessToken(
            subaccount.account_sid,
            subaccount.api_key,
            subaccount.api_secret,
            identity=f'{user_identity}:{device_id}',
            ttl=access_token_ttl
        )
        
        chat_access_token = AccessToken(
            subaccount.account_sid,
            subaccount.api_key,
            subaccount.api_secret,
            identity=user_identity,
            ttl=access_token_ttl
        )
        chat_grant = ChatGrant(service_sid=subaccount.conversation_service_sid)
        chat_access_token.add_grant(chat_grant)

        voice_grant = VoiceGrant(
            outgoing_application_sid=subaccount.twiml_app_sid,
            incoming_allow=True,  # Optional: add to allow incoming calls
        )
        access_token.add_grant(voice_grant)

        sync_grant = SyncGrant(
            service_sid = subaccount.sync_service_sid,
        )
        access_token.add_grant(sync_grant)
        sync_access_token.add_grant(sync_grant)
        
        call_log_sync_grant = SyncGrant(
            service_sid = subaccount.call_logs_sync_service_sid,
        )
        
        call_log_sync_access_token.add_grant(call_log_sync_grant)

        return {
            'user': {
                'identity': user_identity
            },
            'device_id': device_id,
            'device_access_token': access_token.to_jwt(), 
            'sync_access_token': sync_access_token.to_jwt(),
            'call_log_sync_access_token': call_log_sync_access_token.to_jwt(),
            'chat_access_token': chat_access_token.to_jwt(),
            'sync_list_call_obj_template': AppHelper().get_sync_list_call_obj_template(),
        }
        