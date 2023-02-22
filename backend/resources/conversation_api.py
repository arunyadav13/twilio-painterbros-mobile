from flask import request
from flask_restful import Resource
from helpers.db_helper import DBHelper

class ConversationWebhookApi(Resource):
    def post(self):
        tenant_id = request.args.get('tenant_id', None)
        subtenant_id = request.args.get('subtenant_id', None)
        event_type = request.form.get('EventType', None)
        
        db_helper = DBHelper()
        switch = {
            'onConversationAdded': db_helper.add_conversation,
            'onParticipantAdded': db_helper.add_participant,
            'onParticipantRemoved': db_helper.delete_participant,
            'onMessageAdded': db_helper.add_sms_log,
            'onDeliveryUpdated': db_helper.on_delivery_updated
        }
        switch.get(event_type, lambda data : data)(request.form, tenant_id, subtenant_id)
        return 'success'
        
           
class SMSConversationApi(Resource):
    def post(self):
        try:
            participant_attrs = request.get_json()
            if not participant_attrs:
                return {'message': 'Missing required parameters.'}, 400

            conversations_list = DBHelper().get_sms_conversations_list({'participant': participant_attrs})
            return conversations_list            
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500

class ConversationsByParticipantNumbersApi(Resource):
    def post(self):
        try:
            input = request.get_json()
            tenant_id = input.get('tenant_id', None)
            subtenant_id = input.get('subtenant_id', None)
            participant_list = input.get('participants', None)

            if not tenant_id and not subtenant_id and not participant_list:
                return {'message': 'Kindly fill out the mandatory fields'}, 400

            subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
            conversations = DBHelper().get_sms_conversations_list({'conversation': {'subaccount_id': subaccount['id']}})

            response = list()
            for conversation in conversations:
                participant_identities_or_numbers = list()
                for participant in conversation['participants']:
                    if participant['identity']:
                        participant_identities_or_numbers.append('+' + participant['identity'])
                    else:
                        participant_identities_or_numbers.append(participant['address'])

                if len(participant_list) == len(participant_identities_or_numbers):
                    participant_list.sort()
                    participant_identities_or_numbers.sort()

                    both_lists_are_identical = True
                    for i in range(0, len(participant_list)):
                        if (participant_list[i] != participant_identities_or_numbers[i]):
                            both_lists_are_identical = False
                            break

                    if both_lists_are_identical:
                        response.append(conversation)

            return response

        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500
        
class SMSApi(Resource):
    def get(self):
        try:
            conversation_sid = request.args.get('conversation_sid', None)
            if not conversation_sid:
                return {'message': 'Kindly fill out the mandatory fields'}, 400
            
            sms_list = DBHelper().get_messages_list(conversation_sid)
            return sms_list
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500
