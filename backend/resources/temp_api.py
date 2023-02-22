from flask_restful import Resource
from flask import request
from helpers.twilio_helper import TwilioHelper
from helpers.db_helper import DBHelper
from models.conversation import Conversation, ConversationParticipant, ConversationMessage
from models.call import CallLog, Voicemail
from config.db import db

class ResetApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)

        reset = input.get('reset', None)
        if reset:
            reset_conversations = reset.get('conversations', False)
            reset_call_sync_items = reset.get('call_sync_items', False)
            reset_call_log_sync_items = reset.get('call_log_sync_items', False)

            twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
            subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})

            deleted_conversation_count = 0
            deleted_call_sync_lists_count = 0
            deleted_call_sync_docs_count = 0
            deleted_calllog_sync_lists_count = 0

            if reset_conversations:
                conversations = twilio_helper.list_conversations(subaccount['conversation_service_sid'], {'limit': 999})
                for conversation in conversations:
                    twilio_helper.delete_conversation(subaccount['conversation_service_sid'], conversation.sid)
                    deleted_conversation_count += 1

                ConversationMessage.query.delete(synchronize_session=False)
                ConversationParticipant.query.delete(synchronize_session=False)
                Conversation.query.delete(synchronize_session=False)
                db.session.commit()

            if reset_call_sync_items:
                sync_lists = twilio_helper.list_sync_lists(subaccount['sync_service_sid'], {'limit':99})
                for sync_list in sync_lists:
                    twilio_helper.delete_sync_list(subaccount['sync_service_sid'], sync_list.sid)
                    deleted_call_sync_lists_count += 1
                
                sync_documents = twilio_helper.list_sync_documents(subaccount['sync_service_sid'], {'limit':99})
                for sync_document in sync_documents:
                    twilio_helper.delete_sync_document(subaccount['sync_service_sid'], sync_document.sid)
                    deleted_call_sync_docs_count += 1

            if reset_call_log_sync_items:
                sync_lists = twilio_helper.list_sync_lists(subaccount['call_logs_sync_service_sid'], {'limit':99})
                for sync_list in sync_lists:
                    twilio_helper.delete_sync_list(subaccount['call_logs_sync_service_sid'], sync_list.sid)
                    deleted_calllog_sync_lists_count += 1

                Voicemail.query.delete(synchronize_session=False)
                CallLog.query.delete(synchronize_session=False)
                db.session.commit()

            return {
                'deleted_conversation_count': deleted_conversation_count,
                'deleted_call_sync_lists_count': deleted_call_sync_lists_count,
                'deleted_call_sync_docs_count': deleted_call_sync_docs_count,
                'deleted_calllog_sync_lists_count': deleted_calllog_sync_lists_count
            }
        return 'Nothing to reset'
    
class GetSyncListData(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        user_identity = input.get('user_identity', None)
        
        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        receiver_sync_list_items = None
        try:
            receiver_sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
        except Exception as e:
            print(e)
            
        if receiver_sync_list_items:
            return receiver_sync_list_items[0].data
        else:
            return {}