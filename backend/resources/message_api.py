import json, requests, uuid, time
from flask import request
from flask_restful import Resource
from helpers.twilio_helper import TwilioHelper
from helpers.db_helper import DBHelper
from twilio.base.exceptions import TwilioException
from helpers.twilio_helper import CustomTwilioHttpClient
from helpers.app_helper import AppHelper
from config.constant import SERVER_APP_BASE_URL

class InboundMessageApi(Resource):
    def post(self):
        account_sid = request.form.get('AccountSid')
        from_ = request.form.get('From')
        to = request.form.get('To')
        body = request.form.get('Body')
        
        subaccount = DBHelper().get_subaccount({'account_sid': account_sid})
        twilio_helper = TwilioHelper({'account_sid': subaccount['account_sid'], 'auth_token': subaccount['auth_token'], 'http_client': CustomTwilioHttpClient()})

        conversation_details = None
        url = request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/conversation/by-participant-numbers'
        payload = json.dumps({
        "tenant_id": subaccount['tenant_id'],
        "subtenant_id": subaccount['subtenant_id'],
        "participants": [from_,to]
        })
        headers = {
        'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        response_text = json.loads(response.text)
        if len(response_text) > 0:
            try:
                conversation_details = twilio_helper.fetch_conversation(subaccount['conversation_service_sid'], response_text[0].get('twilio_sid'))
            except TwilioException as e:
                if e.code != 20404:
                    raise

        if not conversation_details:
            db_helper = DBHelper()

            sender_contact = db_helper.get_contact(subaccount['tenant_id'], { 'number': from_ })
            if not sender_contact:
                sender_contact = db_helper.add_contact(subaccount['tenant_id'], { 'number': from_ })

            receiver_contact = db_helper.get_contact(subaccount['tenant_id'], { 'number': to })
            if not receiver_contact:
                receiver_contact = db_helper.add_contact(subaccount['tenant_id'], { 'number': to })

            receiver_identity = AppHelper().get_user_identity(receiver_contact['number'])

            participants = dict()
            sender = dict()
            sender['name'] = sender_contact['name']
            sender['number'] = sender_contact['number']
            sender['identity'] = ''
            sender['sms_consent'] = sender_contact['sms_consent']
            participants['sender'] = sender

            receiver = dict()
            receiver['name'] = receiver_contact['name']
            receiver['number'] = receiver_contact['number']
            receiver['identity'] = receiver_identity
            receiver['sms_consent'] = receiver_contact['sms_consent']
            participants['receiver'] = receiver

            conversation_attributes = json.dumps(
                {
                    'participants': participants
                }
            )
            unique_name = str(uuid.uuid4())
            conversation_details = twilio_helper.create_conversation(
                                    subaccount['conversation_service_sid'],
                                    {
                                        'friendly_name': unique_name,
                                        'unique_name': unique_name,
                                        'messaging_service_sid': subaccount['messaging_service_sid'],
                                        'attributes': conversation_attributes
                                    })

            twilio_helper.create_conversation_participant(
                subaccount['conversation_service_sid'],
                conversation_details.sid,
                {
                    'messaging_binding_address': from_,
                    'messaging_binding_proxy_address': to
                }
            )
            twilio_helper.create_conversation_participant(
                subaccount['conversation_service_sid'],
                conversation_details.sid,
                {
                    'identity': receiver_identity
                }
            )

            time.sleep(10)
            twilio_helper.create_conversation_message(
                subaccount['conversation_service_sid'],
                conversation_details.sid,
                {
                    'author': from_,
                    'body': body
                }
            )

        return 'success'