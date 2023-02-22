import uuid, urllib.parse, copy
from flask import Response, request
from datetime import datetime
from helpers.constants import Constants
from helpers.db_helper import DBHelper
from helpers.twilio_helper import TwilioHelper
from helpers.constants import Constants
from twilio.base.exceptions import TwilioException
from config.constant import SERVER_NAME, SERVER_APP_BASE_URL, NCAMEO_API_BASE_URL
import json, requests
from twilio.twiml.voice_response import VoiceResponse

class AppHelper:
    
    def get_sync_list_call_obj_template(self):
        sync_list_call_obj_template = {
            "call": {
                "sid": "",
                "direction": ""
            },
            "conference":{
                "sid": "",
                "status":"initiated",
                "startTime": "",
                "participants": [
                    {
                        "direction": "",
                        "callSid": "",
                        "name": "",
                        "to": "",
                        "from_": "",
                        "startTime": 0,
                        "callStatus": "",
                        "onMute": 0,
                        "onHold": 0,
                        "type": "",
                    } 
                ]
            },
            "warmTransfer":{
                "status": "NA"
            }
        }

        return sync_list_call_obj_template

    def get_user_identity(self, number_or_client_id):
        number = number_or_client_id.replace('client:', '')
        number = number if '+' in number else '+' + number
        phone_number = DBHelper().get_phone_number(number)
        if phone_number:
            user_identity = phone_number['number'].replace('+','')
            return user_identity
        return ''
    
    def prepare_dialing_sequence(self, number, dialing_sequence, unique_internal_phone_numbers, parent_call_forwarding_rule = None, call_durations = None, is_recursive = False):
        phone_number = DBHelper().get_phone_number(number)
        if phone_number:
            # TODO: add logic to avoid loop during call forwarding (if one extension has another extension as forwarding rule)
            call_forwardings = DBHelper().get_call_forwarding_rules({'phone_number_id': phone_number['id']})
            if call_forwardings:
                # get nested call fordwaring rules recursively.
                for call_forwarding in call_forwardings:
                    if not is_recursive:
                        call_durations = {
                            'max_allowed': call_forwarding['duration'],
                            'consumed' : 0
                        }
                    if call_forwarding['number_type'] == Constants.PhoneNumberTypes.INTERNAL.name:
                        if call_forwarding['number'] not in unique_internal_phone_numbers:
                            unique_internal_phone_numbers.append(call_forwarding['number'])
                            self.prepare_dialing_sequence(call_forwarding['number'], dialing_sequence, unique_internal_phone_numbers, call_forwarding, call_durations, True)
                    else:
                        remaining_duration = call_durations['max_allowed'] - call_durations['consumed']
                        if remaining_duration > 0:
                            if remaining_duration < call_forwarding['duration']:
                                call_forwarding['duration'] = remaining_duration
                            dialing_sequence.append(call_forwarding)
                            call_durations['consumed'] = call_durations['consumed'] + call_forwarding['duration']
            else:
                if parent_call_forwarding_rule:
                    # child extension does not have any active call fordwaring rules, add the parent rule.
                    remaining_duration = call_durations['max_allowed'] - call_durations['consumed']
                    if remaining_duration > 0:
                        if remaining_duration < parent_call_forwarding_rule['duration']:
                            parent_call_forwarding_rule['duration'] = remaining_duration
                        dialing_sequence.append(parent_call_forwarding_rule)
                        call_durations['consumed'] = call_durations['consumed'] + parent_call_forwarding_rule['duration']
                else:
                    # top level extension does not have any active call fordwaring rules, add the current extension details as SELF rule.
                    dialing_sequence.append({
                        'id': 0,
                        'number': str(number),
                        'number_type': Constants.PhoneNumberTypes.SELF.name,
                        'duration': 60,
                        'status': Constants.Status.ACTIVE.value
                    })
        else:
            dialing_sequence.append({
                'id': 0,
                'number': str(number),
                'number_type': Constants.PhoneNumberTypes.EXTERNAL.name,
                'duration': 60,
                'status': Constants.Status.ACTIVE.value
            })

    def process_dialing_sequence(self, conference_sid, subaccount, from_, twilio_number, source_call_sid):

        sync_document_unique_name = "ET" + conference_sid

        twilio_helper = TwilioHelper({'tenant_id': subaccount['tenant_id'], 'subtenant_id': subaccount['subtenant_id']})
        sync_document = twilio_helper.fetch_sync_document(subaccount['sync_service_sid'], sync_document_unique_name)

        dialing_sequence = sync_document.data.get('dialing_sequence', None)

        if dialing_sequence and len(dialing_sequence) > 0:
            destination = dialing_sequence[0]
            user_identity = self.get_user_identity(str(destination['number']))

            perticipant = dict()
            perticipant['number'] = str(destination['number'])
            perticipant['duration'] = destination['duration']
            perticipant['label'] = str(uuid.uuid4())

            if destination['number_type'] in (Constants.PhoneNumberTypes.SELF.name, Constants.PhoneNumberTypes.INTERNAL.name):
                perticipant['to_'] = 'client:' + user_identity
                perticipant['from_'] = from_
            else:
                perticipant['to_'] = str(destination['number'])
                perticipant['from_'] = twilio_number

            conference_callback_url = SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/inbound/conference/create-participant/status-callback' \
                +'?source_call_sid='+urllib.parse.quote(source_call_sid) \
                +'&from_='+urllib.parse.quote(from_) \
                +'&tenant_id='+urllib.parse.quote(subaccount['tenant_id']) \
                +'&subtenant_id='+urllib.parse.quote(subaccount['subtenant_id']) \
                +'&user_identity='+urllib.parse.quote(user_identity) \
                +'&conference_sid='+urllib.parse.quote(conference_sid) \
                +'&participant_label='+urllib.parse.quote(perticipant['label']) \
                +'&twilio_number='+urllib.parse.quote(twilio_number)

            max_call_and_ring_duration = self.get_max_call_and_ring_duration(subaccount['tenant_id'])
            twilio_helper.create_conference_participant(conference_sid, {
                'label': perticipant['label'],
                'from_': perticipant['from_'],
                'to': perticipant['to_'],
                'early_media': True,
                'beep': 'onEnter',
                'end_conference_on_exit': False,
                'status_callback': conference_callback_url,
                'status_callback_method': 'POST',
                'status_callback_event': ['initiated', 'ringing', 'answered', 'completed'],
                'timeout': max_call_and_ring_duration['ring'],
                'time_limit': max_call_and_ring_duration['call']
            })

            sync_document.data['processed_destinations'].append(destination)
            del sync_document.data['dialing_sequence'][0]
            twilio_helper.update_sync_document(subaccount['sync_service_sid'], sync_document_unique_name, {"data": sync_document.data})

            return destination
        return {}

    def record_voicemail(self, subaccount, call_sid_to_record, phone_number, text_to_say='', audio_to_play=''):
        response = VoiceResponse()

        if text_to_say:
            response.say(text_to_say)

        if audio_to_play:
            response.play(audio_to_play)

        kwargs = {
            'action': SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/voicemail/recording/complete',
            'method': 'POST',
            'finish_on_key': '#',
            'play_beep': True,
            'transcribe': True,
            'transcribe_callback': SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/voicemail/transcription/complete?tenant_id='+urllib.parse.quote(subaccount['tenant_id'])+'&subtenant_id='+urllib.parse.quote(subaccount['subtenant_id']),
            'max_length': 120,
            'recording_status_callback': SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/voicemail/recording/status-callback?phone_number='+urllib.parse.quote(phone_number)+'&tenant_id='+urllib.parse.quote(subaccount['tenant_id'])+'&subtenant_id='+urllib.parse.quote(subaccount['subtenant_id'])
        }
        response.record(**kwargs)

        twilio_helper = TwilioHelper({'tenant_id': subaccount['tenant_id'], 'subtenant_id': subaccount['subtenant_id']})
        twilio_helper.update_call(call_sid_to_record, {"twiml":response})

    def push_call_log_to_sync_list(self, conference_sid):
        db_helper = DBHelper()
        call_log = db_helper.get_consolidated_call_log(conference_sid)
        if call_log:
            sync_list_item_data = {
                'source':{
                    'name': call_log['source_name'] if call_log['source_name'] else call_log['source_number'],
                    'number': call_log['source_number']
                },
                'destination':{
                    'name': call_log['destination_name'] if call_log['destination_name'] else call_log['destination_number'],
                    'number': call_log['destination_number']
                },
                'direction': call_log['direction'],
                'duration': call_log['call_duration'],
                'timestamp': str(call_log['timestamp']),
                'callStatus': call_log['call_status'],
                'callSId': call_log['call_sid'],
                'isRead': True if call_log['call_status'] == 'completed' and call_log['direction'] == 'outbound-api' else False,
                'forwarding': None
            }
            twilio_helper = TwilioHelper({'tenant_id': call_log['subaccount']['tenant_id'], 'subtenant_id': call_log['subaccount']['subtenant_id']})
            if call_log['direction'] == 'inbound':
                sync_list_name = self.get_user_identity(call_log['destination_number'])
                
                sync_document = twilio_helper.fetch_sync_document(call_log['subaccount']['sync_service_sid'], "ET" + conference_sid)
                all_processed_destinations = sync_document.data.get('processed_destinations')
                current_element = None
                for processed_destination in all_processed_destinations:
                    if processed_destination['number'] == call_log['destination_number']:
                        current_element = processed_destination
                        break
                if len(all_processed_destinations) > 1:
                    sync_list_item_data['forwarding'] = dict()
                    sync_list_item_data['forwarding']['from'] = None
                    sync_list_item_data['forwarding']['to'] = None
                    sync_list_item_data['forwarding']['answewredBy'] = None
                    sync_list_item_data['forwarding']['voicemail'] = None
                    forwarding_from_index = all_processed_destinations.index(current_element)-1     
                    if forwarding_from_index >= 0:
                        from_number = all_processed_destinations[forwarding_from_index].get('number')
                        from_contact = db_helper.search_contact(call_log['subaccount']['tenant_id'], from_number)
                        sync_list_item_data['forwarding']['from'] = {
                            'name': from_contact[0]['name'] if from_contact else from_number,
                            'number': from_number
                        }  
                    forwarding_to_index = all_processed_destinations.index(current_element)+1             
                    if forwarding_to_index < len(all_processed_destinations):
                        to_number = all_processed_destinations[forwarding_to_index].get('number')
                        to_contact = db_helper.search_contact(call_log['subaccount']['tenant_id'], to_number)
                        sync_list_item_data['forwarding']['to'] ={
                            'name': to_contact[0]['name'] if to_contact else to_number,
                            'number': to_number
                        }
            else:
                sync_list_name = self.get_user_identity(call_log['source_number'])
    
            sync_list_sid = None
            try:
                sync_list = twilio_helper.fetch_sync_list(call_log['subaccount']['call_logs_sync_service_sid'], sync_list_name)
                sync_list_sid = sync_list.sid
            except TwilioException as e:
                if e.code != 20404:
                    raise
            if not sync_list_sid:
                api_response = twilio_helper.create_sync_list(call_log['subaccount']['call_logs_sync_service_sid'], {'unique_name': sync_list_name})
                sync_list_sid = api_response.sid
            
            twilio_helper.create_sync_list_item(call_log['subaccount']['call_logs_sync_service_sid'], sync_list_sid, {
            'data': sync_list_item_data
            })
            
            payload = json.dumps({"parameters": {}, "payload": {
                "FromPhone": call_log['source_number'],
                "ToPhone": call_log['destination_number'],
                "CallTimestamp": str(call_log['timestamp'].timestamp() * 1000),
                "VoicemailUrl": None,
                "CallSid": call_log['call_sid'],
                "contact_name": None,
                "Direction": call_log['direction'],
                "Status": call_log['call_status'],
                "Duration": call_log['call_duration']
            }})
            headers = {
                'Content-Type': 'application/json'
            }
            requests.request("POST", NCAMEO_API_BASE_URL + "/twilio/twilioinsertcalllog", headers=headers, data=payload).json()
        return 'success'
    
    def push_voicemail_to_sync_list(self, call_sid):
        db_helper = DBHelper()
        voicemail = db_helper.get_voicemail({'call_sid': call_sid})
        if voicemail and voicemail.get('call_log'):
            blob_url = request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/azure/blob/link?path=' + voicemail['s3_path']
            twilio_helper = TwilioHelper({'tenant_id': voicemail['call_log']['subaccount']['tenant_id'], 'subtenant_id': voicemail['call_log']['subaccount']['subtenant_id']})
            voicemail_contact = db_helper.search_contact(voicemail['call_log']['subaccount']['tenant_id'], voicemail['call_log']['destination_number'])
            call_logs = db_helper.get_call_logs({'source_call_sid': voicemail['call_log']['source_call_sid']})
            for call_log in call_logs:
                sync_list_items = twilio_helper.get_sync_list_items(call_log['subaccount']['call_logs_sync_service_sid'], call_log['destination_number'].replace('+', ''), {})
                for sync_list_item in sync_list_items:
                    if sync_list_item.data.get('callSId') in call_log['call_sid']:
                        data = sync_list_item.data
                        if not data['forwarding']:
                            data['forwarding']=dict()
                            data['forwarding']['from'] = None
                            data['forwarding']['to'] = None
                            data['forwarding']['answewredBy'] = None
                        data['forwarding']['voicemail'] = {
                            'url': blob_url if voicemail['call_log']['call_sid']==sync_list_item.data.get('callSId') else None,
                            'isRead': False,
                            'name': voicemail_contact[0]['name'] if voicemail_contact else voicemail['call_log']['destination_number'],
                            'number': voicemail['call_log']['destination_number']
                        }
                        twilio_helper.update_sync_list_item(call_log['subaccount']['call_logs_sync_service_sid'], call_log['destination_number'].replace('+', ''), sync_list_item.index, {'data': data})
                        break
            db_helper.update_call_log({'call_sid': voicemail['call_log']['call_sid'], 'voicemail_url': blob_url, 'status': voicemail['call_log']['call_status']})
        return 'success'
    
    def update_call_forwarding_details_on_call_log(self, subaccount, conference_sid, source_call_sid):
        db_helper = DBHelper()
        twilio_helper = TwilioHelper({'tenant_id': subaccount['tenant_id'], 'subtenant_id': subaccount['subtenant_id']})
        sync_document = twilio_helper.fetch_sync_document(subaccount['sync_service_sid'], "ET" + conference_sid)
        processed_destinations = sync_document.data.get('processed_destinations')
        if len(processed_destinations) > 1:
            last_element = processed_destinations[-1]
            processed_destinations.pop()
            call_sids = db_helper.get_call_sids_by_source_call_sid(source_call_sid)
            for i in range(len(processed_destinations)):
                sync_list_items = list()
                try:
                    sync_list_items = twilio_helper.get_sync_list_items(subaccount['call_logs_sync_service_sid'], processed_destinations[i].get('number').replace('+', ''), {})
                except Exception as e:
                    # if e.code != 20404:
                    #     raise
                    pass
                for sync_list_item in sync_list_items:
                    if sync_list_item.data.get('callSId') in call_sids:
                        answered_by_contact = db_helper.search_contact(subaccount['tenant_id'], last_element['number'])
                        data = sync_list_item.data
                        data['forwarding']['answewredBy'] = {
                            'name': answered_by_contact[0]['name'] if answered_by_contact else last_element['number'],
                            'number': last_element['number']
                        } 
                        twilio_helper.update_sync_list_item(subaccount['call_logs_sync_service_sid'], processed_destinations[i].get('number').replace('+', ''), sync_list_item.index, {'data': data})
                        break
        return 'success' 
    
    def ivr_for_new_lead(self, subaccount):
        response = VoiceResponse()
        if subaccount['ivr_flow_sid']:
            redirect_url = 'https://webhooks.twilio.com/v1/Accounts/'+subaccount['account_sid']+'/Flows/' + subaccount['ivr_flow_sid']
            response.redirect(redirect_url)
        else:
            response.say('IVR is not configured properly, please contact administrator')
        return Response(str(response), mimetype='text/xml')
    
    def get_max_call_and_ring_duration(self, tenant_id):
        result = {
            'call': 3600,
            'ring': 120
        }
        max_call_duration_db = DBHelper().get_account_settings(tenant_id, 'max-call-duration')
        if max_call_duration_db and max_call_duration_db['value']:
            try:
                max_call_duration = int(max_call_duration_db['value'])
                if max_call_duration > 0 and max_call_duration <= 86400:
                    result['call'] = max_call_duration
            except ValueError:
                pass

        max_ring_duration_db = DBHelper().get_account_settings(tenant_id, 'max-ring-duration')
        if max_ring_duration_db and max_ring_duration_db['value']:
            try:
                max_ring_duration = int(max_ring_duration_db['value'])
                if max_ring_duration > 0 and max_ring_duration <= 600:
                    result['ring'] = max_ring_duration
            except ValueError:
                pass
        return result