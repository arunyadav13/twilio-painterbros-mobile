from flask_restful import Resource
from flask import request
from helpers.twilio_helper import TwilioHelper
from helpers.db_helper import DBHelper

class SyncServiceWebhookApi(Resource):
    def post(self):
        event_type = request.values.get('EventType', None)
        
        if event_type == 'list_item_removed':
            try:
                sync_service_sid = request.values.get('ServiceSid', None)
                sync_list_sid = request.values.get('ListSid', None)

                subaccount = DBHelper().get_subaccount({'sync_service_sid': sync_service_sid})
                twilio_helper = TwilioHelper({'tenant_id': subaccount['tenant_id'], 'subtenant_id': subaccount['subtenant_id']})

                sync_list_items = twilio_helper.get_sync_list_items(sync_service_sid, sync_list_sid, {'limit':99})
                if len(sync_list_items) == 0:
                    twilio_helper.delete_sync_list(sync_service_sid, sync_list_sid)

            except Exception as e:
                pass

        if event_type == 'list_removed':
            try:
                sync_service_sid = request.values.get('ServiceSid', None)
                sync_document_unique_name = request.values.get('ListUniqueName', None)

                subaccount = DBHelper().get_subaccount({'sync_service_sid': sync_service_sid})
                twilio_helper = TwilioHelper({'tenant_id': subaccount['tenant_id'], 'subtenant_id': subaccount['subtenant_id']})

                twilio_helper.update_sync_document(subaccount['sync_service_sid'], sync_document_unique_name, {"data": { "primaryDeviceId": None }})

            except Exception as e:
                pass

        # if event_type == "endpoint_disconnected":
        #     """
        #     This endpoint gets executed when a worker goes offline.
        #     The following logic would restore the Sync Lists and Docucment of
        #     the worker to the default value.
        #     """
        #     try:
        #         pass
        #         # subaccount = DBHelper().get_subaccount({'sync_service_sid': sync_service_sid})
        #         # twilio_helper = TwilioHelper({'tenant_id': subaccount['tenant_id'], 'subtenant_id': subaccount['subtenant_id']})
                
        #         # TODO: when worker goes offline unexpectedly (during an active call)
        #     except Exception as e:
        #         pass
        
        return {'data':{'message':'success'}}