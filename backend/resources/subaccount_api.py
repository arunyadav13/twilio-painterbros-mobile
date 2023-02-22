from flask import request
from flask_restful import Resource
from helpers.twilio_helper import TwilioHelper
from helpers.db_helper import DBHelper
from twilio.base.exceptions import TwilioException
from models.subaccount import SubAccount
from models.emergency_address import EmergencyAddress
from config.constant import SERVER_APP_BASE_URL, TWILIO_MAIN_ACCOUNT_SID, TWILIO_MAIN_ACCOUNT_AUTH_TOKEN, TWILIO_MAIN_ACCOUNT_A2P_10DLC_BRAND_REGISTRATION_SID
from datetime import datetime
import os

class SubAccountApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        kwargs = input.get('kwargs', None)
        if not subtenant_id or not tenant_id:
            return {'message': 'Kindly fill out the mandatory fields'} ,400
        api_response = dict()
        try:
            # Create Sub Account
            db_helper = DBHelper()
            twilio_helper = TwilioHelper({'account_sid': TWILIO_MAIN_ACCOUNT_SID, 'auth_token': TWILIO_MAIN_ACCOUNT_AUTH_TOKEN})
            subaccount = db_helper.get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
            found_subaccount = False
            if subaccount:
                try:
                    twilio_subaccount = twilio_helper.fetch_subaccount(subaccount['account_sid'])
                    if twilio_subaccount and twilio_subaccount.status == 'active':
                        found_subaccount = True
                except TwilioException as e:
                    if e.code != 20404:
                        raise
            
            if not found_subaccount:
                if subaccount:
                    db_helper.delete_subaccount(subaccount['account_sid'])
                subaccount_api_response = twilio_helper.create_subaccount({'friendly_name': tenant_id + ': ' + subtenant_id})
                subaccount = db_helper.add_subaccount(tenant_id, subtenant_id, subaccount_api_response)
                
            api_response['data'] = {
                    'account_sid': subaccount['account_sid']
                }
            twilio_helper = TwilioHelper({'account_sid': subaccount['account_sid'], 'auth_token': subaccount['auth_token']})
            error_messages = list()
            
            # Create Messaging Service   
            try:
                found_messaging_service_sid = False
                if subaccount['messaging_service_sid']:
                    try:
                        twilio_helper.fetch_messaging_service(subaccount['messaging_service_sid'])
                        found_messaging_service_sid = True
                    except TwilioException as e:
                        if e.code != 20404:
                            raise
                if not found_messaging_service_sid:
                    messaging_service_api_response = twilio_helper.create_messaging_service({
                            'friendly_name': subtenant_id,
                            'use_inbound_webhook_on_number': True
                            })
                    subaccount['messaging_service_sid'] = messaging_service_api_response.sid
            except Exception as e:
                error_messages.append(str(e))
            
            # Create SMS Campaign   
            # TODO Remove this if condition once the campaign is ready on regalix account
            if TWILIO_MAIN_ACCOUNT_A2P_10DLC_BRAND_REGISTRATION_SID:
                try:
                    found_a2p_10dlc_campaign_sid = False
                    if subaccount['a2p_10dlc_campaign_sid']:
                        try:
                            twilio_helper.fetch_campaign(subaccount['messaging_service_sid'], subaccount['a2p_10dlc_campaign_sid'])
                            found_a2p_10dlc_campaign_sid = True
                        except TwilioException as e:
                            if e.code != 20404:
                                raise
                    if not found_a2p_10dlc_campaign_sid:
                        campaign_kwargs = {
                            'opt_in_keywords': ['START'],
                            'opt_in_message': 'Welcome to Painter Bros! You are now receiving text message communications. If you\'d like to stop receiving messages at any time, please reply with STOP',
                            'opt_out_keywords': ['STOP'],
                            'opt_out_message': 'You have successfully been unsubscribed. You will not receive any more messages from this number. Reply START to resubscribe.',
                            'help_keywords': ['HELP'],
                            'help_message': 'Reply STOP to unsubscribe. Msg&Data Rates May Apply.',
                            'description': 'This campaign sends estimate and final invoice link for approval and payment of job',
                            'message_flow': 'End-users opt in by going to website www.painterbros.com and fill out estimation form with contact information, including phone number, where they will "Agree to receive communication via text message."',
                            'message_samples': ['Welcome to Painter Bros! You are now receiving text message communications. If you\'d like to stop receiving messages at any time, please reply with STOP', 'You have successfully been unsubscribed. You will not receive any more messages from this number. Reply START to resubscribe.'],
                            'us_app_to_person_usecase': 'CUSTOMER_CARE',
                            'has_embedded_links': True,
                            'has_embedded_phone': True,
                            'brand_registration_sid': TWILIO_MAIN_ACCOUNT_A2P_10DLC_BRAND_REGISTRATION_SID,
                        }
                        campaign_api_response = twilio_helper.create_campaign(subaccount['messaging_service_sid'], campaign_kwargs)
                        subaccount['a2p_10dlc_campaign_sid'] = campaign_api_response.sid
                except TwilioException as e:
                    error_messages.append(str(e.msg))
                except Exception as e:
                    error_messages.append(str(e))

            # Create TwiML app    
            try:
                found_twiml_app = False
                if subaccount['twiml_app_sid']:
                    try:
                        twilio_helper.fetch_twiml_app(subaccount['twiml_app_sid'])
                        found_twiml_app = True
                    except TwilioException as e:
                        if e.code != 20404:
                            raise
                if not found_twiml_app:
                    twiml_app_api_response = twilio_helper.create_twiml_app({
                            'friendly_name': subtenant_id,
                            'voice_method': 'POST',
                            'voice_url': request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/call/outbound'
                            })
                    subaccount['twiml_app_sid'] = twiml_app_api_response.sid
            except Exception as e:
                error_messages.append(str(e))
                
            
            # Create Sync Service  
            try:
                found_sync_service = False
                if subaccount['sync_service_sid']:
                    try:
                        twilio_helper.fetch_sync_service(subaccount['sync_service_sid'])
                        found_sync_service = True
                    except TwilioException as e:
                        if e.code != 20404:
                            raise
                if not found_sync_service:
                    sync_service_api_response = twilio_helper.create_sync_service({
                        'friendly_name': 'calls',
                        'webhooks_from_rest_enabled': True,
                        'reachability_webhooks_enabled': True,
                        'reachability_debouncing_enabled': True,
                        'reachability_debouncing_window': 2000,
                        'webhook_url': request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/sync/webhook'
                    })
                    subaccount['sync_service_sid'] = sync_service_api_response.sid
            except Exception as e:
                error_messages.append(str(e))
            
            # Create Sync Service for call logs  
            try:
                found_call_logs_sync_service = False
                if subaccount['call_logs_sync_service_sid']:
                    try:
                        twilio_helper.fetch_sync_service(subaccount['call_logs_sync_service_sid'])
                        found_call_logs_sync_service = True
                    except TwilioException as e:
                        if e.code != 20404:
                            raise
                if not found_call_logs_sync_service:
                    call_logs_sync_service_api_response = twilio_helper.create_sync_service({
                        'friendly_name': 'call-logs',
                        'webhooks_from_rest_enabled': True,
                        'reachability_webhooks_enabled': False,
                        'reachability_debouncing_enabled': False,
                        'reachability_debouncing_window': 2000,
                        'webhook_url': request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/sync/webhook'
                    })
                    subaccount['call_logs_sync_service_sid'] = call_logs_sync_service_api_response.sid
            except Exception as e:
                error_messages.append(str(e))
                
            # Create API Key   
            try:
                found_api_key = False
                if subaccount['api_key']:
                    try:
                        twilio_helper.fetch_api_key(subaccount['api_key'])
                        found_api_key = True
                    except TwilioException as e:
                        if e.code != 20404:
                            raise
                if not found_api_key:
                    api_key_api_response = twilio_helper.create_api_key({
                            'friendly_name': subtenant_id
                            })
                    subaccount['api_key'] = api_key_api_response.sid
                    subaccount['api_secret'] = api_key_api_response.secret
            except Exception as e:
                error_messages.append(str(e))
                
            # Create Conversation Service 
            try:
                found_conversation_service = False
                if subaccount['conversation_service_sid']:
                    try:
                        twilio_helper.fetch_conversation_service(subaccount['conversation_service_sid'])
                        found_conversation_service = True
                    except TwilioException as e:
                        if e.code != 20404:
                            raise
                if not found_conversation_service:
                    conversation_service_api_response = twilio_helper.create_conversation_service({
                            'friendly_name': subtenant_id
                            })
                    subaccount['conversation_service_sid'] = conversation_service_api_response.sid
            except Exception as e:
                error_messages.append(str(e))
            
            # Update Conversation Webhook
            try:
                twilio_helper.update_conversation_webhook({
                    'post_webhook_url': request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/conversation/webhook?tenant_id=' + tenant_id + '&subtenant_id=' + subtenant_id,
                    'pre_webhook_url': request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/conversation/webhook?tenant_id=' + tenant_id + '&subtenant_id=' + subtenant_id,
                    'method': 'POST',
                    'filters': ['onConversationAdded', 'onParticipantAdded', 'onParticipantRemoved', 'onMessageAdded', 'onDeliveryUpdated'],
                })
            except Exception as e:
                error_messages.append(str(e))
            
            # Create IVR Flow
            try:
                found_ivr_flow = False
                if subaccount['ivr_flow_sid']:
                    try:
                        twilio_helper.fetch_flow(subaccount['ivr_flow_sid'])
                        found_ivr_flow = True
                    except TwilioException as e:
                        if e.code != 20404:
                            raise
                if not found_ivr_flow:
                    current_dir = os.path.dirname(os.path.realpath(__file__))
                    with open(current_dir + '/../templates/ivr/new-leads.json') as f:
                        flow_json = f.read()
                        flow_json = flow_json.replace("{{BASE_URL}}", request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL)
                        ivr_flow_api_response = twilio_helper.create_flow({
                                    'friendly_name': subtenant_id,
                                    'status': 'published',
                                    'definition': flow_json
                                })
                        subaccount['ivr_flow_sid'] = ivr_flow_api_response.sid
            except Exception as e:
                error_messages.append(str(e))
                         
            # Create Emergency Address
            api_response['data']['emergency_address'] = dict()
            try:
                if kwargs:
                    if kwargs.get('iso_country', '').lower().strip() in ['usa', 'united states', 'united states of america', 'us']:
                        kwargs['iso_country'] = 'US'
                    kwargs['emergency_enabled'] = True
                    kwargs['friendly_name'] = subtenant_id
                    found_emergency_address = False
                    emergency_address = DBHelper().get_emergency_address({'subaccount_id': subaccount['id']})
                    if emergency_address:
                        try:
                            twilio_helper.fetch_emergency_addresses(emergency_address['twilio_sid'])
                            found_emergency_address = True
                        except TwilioException as e:
                            if e.code != 20404:
                                raise
                    if not found_emergency_address:
                        emergency_address_api_response = twilio_helper.create_emergency_address(kwargs)
                        emergency_address = db_helper.add_emergency_address(subaccount['id'], emergency_address_api_response)
                    api_response['data']['emergency_address']['is_created'] = True
                    api_response['data']['emergency_address']['sid'] = emergency_address['twilio_sid']
        
            except TwilioException as e:
                api_response['data']['emergency_address']['is_created'] = False
                api_response['data']['emergency_address']['details'] = e.msg
                
            except Exception as e:
                api_response['data']['emergency_address']['is_created'] = False
                api_response['data']['emergency_address']['details'] = str(e)
            
            db_helper.edit_subaccount(subaccount['account_sid'], {
                'messaging_service_sid': subaccount['messaging_service_sid'],
                'twiml_app_sid': subaccount['twiml_app_sid'],
                'sync_service_sid': subaccount['sync_service_sid'],
                'call_logs_sync_service_sid': subaccount['call_logs_sync_service_sid'],
                'api_key': subaccount['api_key'],
                'api_secret': subaccount['api_secret'],
                'conversation_service_sid': subaccount['conversation_service_sid'],
                'a2p_10dlc_campaign_sid': subaccount['a2p_10dlc_campaign_sid'],
                'ivr_flow_sid': subaccount['ivr_flow_sid']
            })
            
            if error_messages:
                return {'message': 'An application error occurred, please contact administrator', 'details': ', '.join(error_messages) }, 500
            return api_response
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500
        
    def put(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        account_status = input.get('account_status', None)
        
        if not subtenant_id or not tenant_id or not account_status:
            return {'message': 'Kindly fill out the mandatory fields'}, 400
        try:
            subaccount = SubAccount.query.filter(SubAccount.tenant_id==tenant_id, SubAccount.subtenant_id==subtenant_id, SubAccount.status!=-1).first()
            if not subaccount:
                return {'message': 'Subaccount does not exist'}, 400
            
            twilio_helper = TwilioHelper({'account_sid': TWILIO_MAIN_ACCOUNT_SID, 'auth_token': TWILIO_MAIN_ACCOUNT_AUTH_TOKEN})
            twilio_helper.update_subaccount(subaccount.account_sid, {'status': account_status})
            subaccount.account_status = account_status
            if account_status == 'active':
                subaccount.status = 1
            elif account_status == 'suspended':
                subaccount.status = 0
            elif account_status == 'closed':
                subaccount.status = -1
                subaccount.deleted_at = datetime.utcnow()
            subaccount.save()
            return {'message':'Subaccount updated successfully'}
        
        except TwilioException as e:
            return {'message': e.msg.replace('Unable to delete record: ', '')}, 417
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500
