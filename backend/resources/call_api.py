import urllib.parse, json, copy, time
from flask import Response, request
from flask_restful import Resource
from twilio.twiml.voice_response import VoiceResponse, Dial
from datetime import datetime
from helpers.app_helper import AppHelper
from helpers.twilio_helper import TwilioHelper
from helpers.db_helper import DBHelper
from config.constant import SERVER_NAME, SERVER_APP_BASE_URL


"""
----------------------------------------------------------------------------------------------
APIs FOR INBOUND CALLS
----------------------------------------------------------------------------------------------
"""
class InboundCallApi(Resource):
    def post(self):
        call_sid = request.values.get('CallSid', None)
        from_ = request.values.get('From', None)
        to = request.values.get('To', None)

        from_number = DBHelper().get_phone_number(from_)
        to_number = DBHelper().get_phone_number(to)
        
        response = VoiceResponse()
        if not to_number:
            response.say('This number does not belongs to any organization')
            return Response(str(response), mimetype='text/xml')

        # TODO: commented temporarily for Feb 10 client demo.
        # if not from_number or from_number['subaccount']['tenant_id'] != to_number['subaccount']['tenant_id']:
        #     pre_lead_or_lead = DBHelper().get_pre_lead_or_lead_by_phone_number(from_)
        #     if not pre_lead_or_lead:
        #         return AppHelper().ivr_for_new_lead(to_number['subaccount'])
            
        dial = Dial()

        conference_callback_url = SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/inbound/conference/status-callback' \
            +'?source_call_sid='+urllib.parse.quote(call_sid) \
            +'&from_='+urllib.parse.quote(from_) \
            +'&to='+urllib.parse.quote(to) \
            +'&tenant_id='+urllib.parse.quote(to_number['subaccount']['tenant_id']) \
            +'&subtenant_id='+urllib.parse.quote(to_number['subaccount']['subtenant_id'])

        dial.conference(
            call_sid,
            status_callback=conference_callback_url,
            status_callback_event='join, leave, end',
            end_conference_on_exit = True,
            start_conference_on_enter = True
        )
        response.append(dial)
        return Response(str(response), mimetype='text/xml')

class InboundCallConferenceStatusCallbackApi(Resource):
    def post(self):
        sequence_number = request.values.get('SequenceNumber', None)
        status_callback_event = request.values.get('StatusCallbackEvent', None)
        conference_sid = request.values.get('ConferenceSid', None)
        participant_label = request.values.get('ParticipantLabel', None)
        
        source_call_sid = request.args.get('source_call_sid', None)
        from_ = request.args.get('from_', None)
        to = request.args.get('to', None)
        tenant_id = request.args.get('tenant_id', None)
        subtenant_id = request.args.get('subtenant_id', None)

        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})

        if sequence_number == '1' and status_callback_event == 'participant-join':
            from_number = DBHelper().get_phone_number(from_)
            to_number = DBHelper().get_phone_number(to)

            unique_internal_phone_numbers = list()
            dialing_sequence = list()

            lead = dict()

            """
            TODO: call flow skip list to be used only for testing. Needs to be removed before UAT.
            """
            skip_the_call_flow_logic = False
            call_flow_skip_list = DBHelper().get_account_settings(to_number['subaccount']['tenant_id'], 'call_flow_skip_list')
            if call_flow_skip_list:
                call_flow_skip_list = call_flow_skip_list['value'].replace(' ', '').split(',')
                skip_the_call_flow_logic = True if from_ in call_flow_skip_list else False

            # TODO: added temporarily for Feb 10 client demo.
            skip_the_call_flow_logic = True

            if skip_the_call_flow_logic:
                AppHelper().prepare_dialing_sequence(to_number['number'], dialing_sequence, unique_internal_phone_numbers)
            else:
                if from_number and to_number and from_number['subaccount']['tenant_id'] == to_number['subaccount']['tenant_id']:
                    AppHelper().prepare_dialing_sequence(to_number['number'], dialing_sequence, unique_internal_phone_numbers)
                else:
                    lead = DBHelper().get_lead_by_phone_number(to)
                    for target in lead['call_flow']['targets']:
                        AppHelper().prepare_dialing_sequence(target['number'], dialing_sequence, unique_internal_phone_numbers)
            
            if len(dialing_sequence) > 0:
                """
                remove duplicate numbers from the dialing_sequences.
                if the caller's number is present in dialing_sequence, remove that as well.
                """
                unique_numbers = list()
                ds = list()
                for destination in dialing_sequence:
                    if destination['number'] != from_ and destination['number'] not in unique_numbers:
                        unique_numbers.append(destination['number'])
                        ds.append(destination)
                dialing_sequence = ds
                
            twilio_helper.create_sync_document(subaccount['sync_service_sid'],
                {
                    "unique_name" : "ET" + conference_sid,
                    "data" : json.dumps(
                        {
                            'user_identity': '',
                            'dialing_sequence': dialing_sequence if dialing_sequence else list(),
                            'voicemail': lead['call_flow']['voicemail'] if lead else dict(),
                            'processed_destinations': list(),
                        }
                    )
                }
            )

            AppHelper().process_dialing_sequence(conference_sid, subaccount, from_, to, source_call_sid)

        if status_callback_event == 'conference-end':
            """
            when a conference on hold state, and the customer disconnects the call, we need know which worker has put the conference on hold  
            the conference event listner will not have any info about the worker since the worker call leg has been disconnected already
            in this scenario, the last user's user_identity needs to be fetched from sync doc.
            """
            sync_document = twilio_helper.fetch_sync_document(subaccount['sync_service_sid'], "ET" + conference_sid)
            user_identity = sync_document.data['user_identity']
            if user_identity:
                sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
                for sync_list_item in sync_list_items:
                    sync_list_item_data = sync_list_item.data
                    if sync_list_item_data['conference']['sid'] == conference_sid:
                        """
                        only when the conference is on hold, the sync list item will get deleted from here.
                        in all other scenarios, it will get deleted from the call completed event handler.
                        """
                        if sync_list_item_data['conference']['status'] in ('hold'):
                            twilio_helper.delete_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index)
                        break

            twilio_helper.update_sync_document(subaccount['sync_service_sid'], "ET" + conference_sid, {'ttl': 60})
            
        return {'data':{'message':'success'}}

class InboundCallConferenceCreateParticipantStatusCallbackApi(Resource):
    def post(self):
        call_status = request.values.get('CallStatus', None)
        call_sid = request.values.get('CallSid', None)
        to = request.values.get('To', None)
        from_ = request.values.get('From', None)

        source_call_sid = request.args.get('source_call_sid', None)
        tenant_id = request.args.get('tenant_id', None)
        subtenant_id = request.args.get('subtenant_id', None)
        user_identity = request.args.get('user_identity', None)
        conference_sid = request.args.get('conference_sid', None)
        participant_label = request.args.get('participant_label', None)
        twilio_number = request.args.get('twilio_number', None)

        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})

        user_identity = AppHelper().get_user_identity(to)

        """
        during an incoming call, create the sync_list, if not exists and if the user is an internal user.
        """
        if user_identity:    
            try:
                twilio_helper.create_sync_list(subaccount['sync_service_sid'], {'unique_name': user_identity})
            except Exception as e:
                pass

        if call_status == 'ringing':
            # create sync list item only for internal numbers
            if user_identity:
                sync_list_item_data = AppHelper().get_sync_list_call_obj_template()
                sync_list_item_data['call']['sid'] = source_call_sid
                sync_list_item_data['call']['direction'] = 'inbound'
                sync_list_item_data['conference']['sid'] = conference_sid
                sync_list_item_data['conference']['status'] = 'ringing'

                """
                Destination node
                """
                destination_node = copy.deepcopy(sync_list_item_data['conference']['participants'][0])
                destination_node['direction'] = 'inbound'
                destination_node['callSid'] = call_sid
                destination_node['name'] = 'client:' + user_identity
                destination_node['to'] = 'client:' + user_identity
                destination_node['from_'] = from_
                destination_node['startTime'] = str(datetime.utcnow())
                destination_node['callStatus'] = 'ringing'
                destination_node['type'] = 'destination'
                sync_list_item_data['conference']['participants'].append(destination_node)

                """
                Source node
                """
                # TODO: Need to check if callee_contact_details is actually required or not
                search_contact_response = DBHelper().search_contact(subaccount['tenant_id'], from_)

                source_node = copy.deepcopy(sync_list_item_data['conference']['participants'][0])
                source_node['direction'] = 'inbound'
                source_node['callSid'] = source_call_sid
                source_node['name'] = search_contact_response[0]['name'] if search_contact_response else from_
                source_node['to'] = to
                source_node['from_'] = from_
                source_node['startTime'] = str(datetime.utcnow())
                source_node['callStatus'] = 'in-progress'
                source_node['type'] = 'source'
                sync_list_item_data['conference']['participants'].append(source_node)

                del sync_list_item_data['conference']['participants'][0]
                twilio_helper.create_sync_list_item(subaccount['sync_service_sid'], user_identity, {'data': sync_list_item_data})

            """
            when a conference on hold state, and the customer disconnects the call, we need know which worker has put the conference on hold  
            the conference event listner will not have any info about the worker since the worker call leg has been disconnected already
            in this scenario, the last user's user_identity needs to be fetched from sync doc.
            """
            sync_document = twilio_helper.fetch_sync_document(subaccount['sync_service_sid'], "ET" + conference_sid)
            sync_document.data['user_identity'] = user_identity
            twilio_helper.update_sync_document(subaccount['sync_service_sid'], "ET" + conference_sid, {"data": sync_document.data})

        if call_status == 'in-progress':
            twilio_helper.update_conference_participant(conference_sid, participant_label, {"end_conference_on_exit":"true"})
            if user_identity:
                sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
                for sync_list_item in sync_list_items:
                    sync_list_item_data = sync_list_item.data
                    if sync_list_item_data['call']['sid'] == source_call_sid:
                        sync_list_item_data['conference']['status'] = 'in-progress'
                        sync_list_item_data['conference']['startTime'] = str(datetime.utcnow())
                        perticipants = sync_list_item_data['conference']['participants']
                        for i, perticipant in enumerate(perticipants):
                            if perticipant['type'] in ('source','destination'):
                                # updating source perticipant status in sync list item json
                                perticipants[i]['callStatus'] = 'in-progress'
                        twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index, {'data':sync_list_item_data})
                        break

            sync_document = twilio_helper.fetch_sync_document(subaccount['sync_service_sid'], "ET" + conference_sid)
            sync_document.data.pop('dialing_sequence')
            twilio_helper.update_sync_document(subaccount['sync_service_sid'], "ET" + conference_sid, {"data": sync_document.data})

            AppHelper().update_call_forwarding_details_on_call_log(subaccount, conference_sid, source_call_sid)
            
        if call_status == 'completed':
            if user_identity:
                sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
                for sync_list_item in sync_list_items:
                    sync_list_item_data = sync_list_item.data
                    if sync_list_item_data['conference']['sid'] == conference_sid:
                        if sync_list_item_data['conference']['status'] not in ('hold'):
                            """
                            sync list item should not get removed after putting a call on hold.
                            in all other scenrios, it will get deleted from here when the call is completed
                            reason: when the conference in not on hold, at first the "conference-end" event will fire and then the call "completed" event will fire.
                            if we delete the sync list item on "conference-end" event, we won't be able to access that sync list item here and an exception will be raised.
                            """
                            twilio_helper.delete_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index)
                        break

        if call_status in ('busy', 'no-answer', 'failed', 'canceled'):
            if user_identity:
                sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
                for sync_list_item in sync_list_items:
                    sync_list_item_data = sync_list_item.data
                    if sync_list_item_data['conference']['sid'] == conference_sid:
                        """
                        since this inbound call api, this logic is only applicable to the primary participant (destination/worker), not for additional participants.
                        """
                        twilio_helper.delete_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index)
                        break

            conference = twilio_helper.fetch_conference(conference_sid)
            if conference and conference.status != 'completed':
                destination = AppHelper().process_dialing_sequence(conference_sid, subaccount, from_, twilio_number, source_call_sid)

                """
                Record voicemail when dialing_sequence is empty.
                """
                if not destination:
                    voicemail_msg = 'Please leave a message after the beep. When you are done, press hash or just hang-up.'
                    voicemail_number = '+' + user_identity
                    sync_document = twilio_helper.fetch_sync_document(subaccount['sync_service_sid'], "ET" + conference_sid)                
                    if sync_document.data['voicemail']:
                        voicemail_number = sync_document.data['voicemail']['number']
                    AppHelper().record_voicemail(subaccount, source_call_sid, voicemail_number, voicemail_msg)
        
        if call_status in ('no-answer', 'busy', 'canceled', 'failed', 'completed'):
            DBHelper().save_call_log(subaccount, request.form, 'inbound', conference_sid, source_call_sid)
            AppHelper().push_voicemail_to_sync_list(call_sid)            
            conference = twilio_helper.fetch_conference(conference_sid)
            if conference and conference.status == 'completed':
                AppHelper().push_call_log_to_sync_list(conference_sid)
        return {'data':{'message':'success'}}

class InboundCallStatusCallbackApi(Resource):
    def post(self):
        return 'success'


"""
----------------------------------------------------------------------------------------------
APIs FOR OUTBOUND CALLs
----------------------------------------------------------------------------------------------
"""
class OutboundCallApi(Resource):
    def post(self):
        call_sid = request.values.get('CallSid', None)
        tenant_id = request.values.get('tenant_id', None)
        subtenant_id = request.values.get('subtenant_id', None)
        user_identity = request.values.get('user_identity', None)

        response = VoiceResponse()
        dial = Dial()

        conference_callback_url = SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/outbound/conference/status-callback' \
            +'?source_call_sid='+urllib.parse.quote(call_sid) \
            +'&tenant_id='+urllib.parse.quote(tenant_id) \
            +'&subtenant_id='+urllib.parse.quote(subtenant_id) \
            +'&user_identity='+urllib.parse.quote(user_identity)

        dial.conference(
            call_sid,
            status_callback=conference_callback_url,
            status_callback_event='join, leave, end',
            end_conference_on_exit = True,
            start_conference_on_enter = True
        )
        response.append(dial)
        return Response(str(response), mimetype='text/xml')

class OutboundCallConferenceStatusCallbackApi(Resource):
    def post(self):
        sequence_number = request.values.get('SequenceNumber', None)
        status_callback_event = request.values.get('StatusCallbackEvent', None)
        conference_sid = request.values.get('ConferenceSid', None)
        call_sid = request.values.get('CallSid', None)
        
        source_call_sid = request.args.get('source_call_sid', None)
        tenant_id = request.args.get('tenant_id', None)
        subtenant_id = request.args.get('subtenant_id', None)
        user_identity = request.args.get('user_identity', None)

        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})

        if sequence_number == '1' and status_callback_event == 'participant-join':
            sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
            for sync_list_item in sync_list_items:
                sync_list_item_data = sync_list_item.data
                if sync_list_item_data['call']['sid'] == source_call_sid:
                    sync_list_item_data['conference']['sid'] = conference_sid

                    perticipants = sync_list_item_data['conference']['participants']
                    for i, perticipant in enumerate(perticipants):
                        if perticipant['type'] == 'source':
                            # updating source perticipant status in sync list item json
                            perticipants[i]['direction'] = 'inbound'
                            perticipants[i]['callSid'] = call_sid
                            perticipants[i]['startTime'] = str(datetime.utcnow())
                            perticipants[i]['callStatus'] = 'in-progress'

                        if perticipant['type'] == 'destination':
                            # sync list item json already has source and destination nodes
                            # adding destination node as perticipant to the conference
                            conference_callback_url = SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/conference/create-participant/status-callback' \
                                +'?source_call_sid='+urllib.parse.quote(source_call_sid) \
                                +'&tenant_id='+urllib.parse.quote(tenant_id) \
                                +'&subtenant_id='+urllib.parse.quote(subtenant_id) \
                                +'&user_identity='+urllib.parse.quote(user_identity) \
                                +'&conference_sid='+conference_sid

                            max_call_and_ring_duration = AppHelper().get_max_call_and_ring_duration(tenant_id)
                            conference_perticipant = twilio_helper.create_conference_participant(
                                conference_sid, {
                                    'from_': perticipant['from_'],
                                    'to': perticipant['to'],
                                    'early_media': True,
                                    'beep': 'onEnter',
                                    'end_conference_on_exit' : True,
                                    'status_callback': conference_callback_url,
                                    'status_callback_method': 'POST',
                                    'status_callback_event': ['initiated', 'ringing', 'answered', 'completed'],
                                    'timeout': max_call_and_ring_duration['ring'],
                                    'time_limit': max_call_and_ring_duration['call']
                                })

                            perticipants[i]['direction'] = 'outbound-api'
                            perticipants[i]['callSid'] = conference_perticipant.call_sid
                            perticipants[i]['startTime'] = str(datetime.utcnow())
                            perticipants[i]['callStatus'] = 'initiated'

                    twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index, {'data':sync_list_item_data})
                    break

        if sequence_number == '2' and status_callback_event == 'participant-leave':
            """
            if destination rejects the call, the "end_conference_on_exit" flag does not end the conference. Hence it needs to be completed manually.
            If source rejects the call, then "end_conference_on_exit" flag ends the conference automatically, hence no need to complete the conference manually. 
            """
            conference = twilio_helper.fetch_conference(conference_sid)
            if conference and conference.status != 'completed':
                twilio_helper.update_conference(conference_sid, {'status':'completed'})

        if status_callback_event == 'conference-end':
            """
            if destination disconnects the call while the call/conference is on hold state, remove the sync list upon conference end.
            """
            if user_identity:
                sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
                for sync_list_item in sync_list_items:
                    sync_list_item_data = sync_list_item.data
                    if sync_list_item_data['conference']['sid'] == conference_sid:
                        """
                        delete the sync list item if the conference is on "hold" state or if warm transfer is completed (to clear the transferer's ui)
                        """
                        if sync_list_item_data['conference']['status'] in ('hold') or sync_list_item_data['warmTransfer']['status'] in ('in-progress'):
                            twilio_helper.delete_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index)
                        break

        return {'data':{'message':'success'}}


"""
----------------------------------------------------------------------------------------------
COMMON APIs FOR BOTH INBOUND & OUTBOUND CALLS
----------------------------------------------------------------------------------------------
"""
class ConferenceCreateParticipantStatusCallbackApi(Resource):
    def post(self):
        call_status = request.values.get('CallStatus', None)
        call_sid = request.values.get('CallSid', None)
        called = request.form.get('Called', '') # TODO: @thas: can it not be "to" and "request.values"?

        tenant_id = request.args.get('tenant_id', None)
        subtenant_id = request.args.get('subtenant_id', None)
        user_identity = request.args.get('user_identity', None)
        conference_sid = request.args.get('conference_sid', None)
        to = request.form.get('To', '') # TODO: can it not be "request.values"?
        
        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})

        if call_status in ('ringing', 'in-progress'):
            if user_identity:
                sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
                for sync_list_item in sync_list_items:
                    sync_list_item_data = sync_list_item.data
                    if sync_list_item_data['conference']['sid'] == conference_sid:
                        perticipants = sync_list_item_data['conference']['participants']
                        for i, perticipant in enumerate(perticipants):
                            if perticipant['callSid'] == call_sid:
                                # updating perticipant status in sync list item json
                                perticipants[i]['callStatus'] = call_status
                                """
                                update the conference status only if the participant type is source or destination, skip for any additional participants
                                """
                                if perticipant['type'] in ('source','destination'):
                                    sync_list_item_data['conference']['status'] = call_status

                                """
                                set the conference start time only for the first "in-progress" event, ignore it during call "resume" operations.
                                """
                                if call_status == 'in-progress' and not sync_list_item_data['conference']['startTime']:
                                    sync_list_item_data['conference']['startTime'] = str(datetime.utcnow())
                        twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index, {'data':sync_list_item_data})
                        break
                    
        if call_status in ('completed', 'busy', 'no-answer', 'failed', 'canceled'):
            if user_identity:
                sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
                for sync_list_item in sync_list_items:
                    sync_list_item_data = sync_list_item.data
                    if sync_list_item_data['conference']['sid'] == conference_sid:
                        if sync_list_item_data['conference']['status'] not in ('hold'):
                            perticipants = sync_list_item_data['conference']['participants']
                            for i, perticipant in enumerate(perticipants):
                                if perticipant['callSid'] == call_sid and perticipant['type'] not in ('source','destination'):
                                    """
                                    if the perticipant type is warm-transfer, then update the status node of "warmTransfer" in sync list item json.
                                    this is to detect if the warm-transfer perticipant has disconnected the call even before the transfer was completed.
                                    hence, keep the "Abort Transfer" button active so that the transferor can abort the transfer which will remove the "hold" from other participants. 
                                    """
                                    if perticipant['type'] == 'warm-transfer':
                                        sync_list_item_data['warmTransfer']['status'] = call_status

                                    """
                                    If the call completed event has fired an additional participant, do not delete the entire sync list item.
                                    Instead, remove the participant node from the sync list JSON.
                                    """
                                    del perticipants[i]
                                    twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index, {'data':sync_list_item_data})
                                    break
                                
                                if perticipant['callSid'] == call_sid and perticipant['type'] in ('source','destination'):
                                    """
                                    sync list item should not get removed after putting a call on hold.
                                    in all other scenrios, it will get deleted from here when the call is completed.
                                    reason: when the conference in not on hold, at first the "conference-end" event will fire and then the call "completed" event will fire.
                                    if we delete the sync list item on "conference-end" event, we won't be able to access that sync list item here and an exception will be raised.
                                    also, do not try to delete the sync list item if warm transfer is in progress because in that case when customer ends the call before the warm transfer is either completed or aborted,
                                    the conference-end event will fire first and the sync list item will be deleted there.
                                    """
                                    if sync_list_item_data['warmTransfer']['status'] not in ('in-progress'):
                                        twilio_helper.delete_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index)
                                    break
                        break

        if call_status in ('busy', 'no-answer', 'failed', 'canceled', 'completed'):
            DBHelper().save_call_log(subaccount, request.form, 'outbound-api', conference_sid)
            conference = twilio_helper.fetch_conference(conference_sid)
            if conference and conference.status == 'completed':
                AppHelper().push_call_log_to_sync_list(conference_sid)

        return {'data':{'message':'success'}}

class ConferenceCreateParticipantApi(Resource):
    def post(self):
        input = request.get_json()
        conference_sid = input.get('conference_sid', None)
        source_call_sid = input.get('source_call_sid', None)
        from_ = input.get('from_', None)
        to = input.get('to', None)
        name = input.get('name', None)
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        user_identity = input.get('user_identity', None)

        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})

        conference_callback_url = SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/conference/create-participant/status-callback' \
            +'?source_call_sid='+urllib.parse.quote(source_call_sid) \
            +'&tenant_id='+urllib.parse.quote(tenant_id) \
            +'&subtenant_id='+urllib.parse.quote(subtenant_id) \
            +'&user_identity='+urllib.parse.quote(user_identity) \
            +'&conference_sid='+conference_sid

        max_call_and_ring_duration = AppHelper().get_max_call_and_ring_duration(tenant_id)
        conference_perticipant = twilio_helper.create_conference_participant(
            conference_sid, {
                'from_': from_,
                'to': to,
                'early_media': True,
                'beep': 'onEnter',
                'end_conference_on_exit' : False,
                'status_callback': conference_callback_url,
                'status_callback_method': 'POST',
                'status_callback_event': ['ringing', 'answered', 'completed'],
                'timeout': max_call_and_ring_duration['ring'],
                'time_limit': max_call_and_ring_duration['call']
            })

        new_participant = AppHelper().get_sync_list_call_obj_template()['conference']['participants'][0]
        new_participant['direction'] = 'outbound-api'
        new_participant['callSid'] = conference_perticipant.call_sid
        new_participant['name'] = name
        new_participant['to'] = to
        new_participant['from_'] = from_
        new_participant['startTime'] = str(datetime.utcnow())
        new_participant['callStatus'] = 'initiated'

        sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
        for sync_list_item in sync_list_items:
            sync_list_item_data = sync_list_item.data
            if sync_list_item_data['call']['sid'] == source_call_sid:
                sync_list_item_data['conference']['participants'].append(new_participant)
                twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index, {'data':sync_list_item_data})
                break

        return {
            'data': {
                'message':'success',
                'perticipant_call_sid' : conference_perticipant.call_sid
            }
        }

class ConferenceRemoveParticipantApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        conference_sid = input.get('conference_sid', None)
        participant_call_sid = input.get('participant_call_sid', None)

        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        twilio_helper.delete_conference_participant(conference_sid, participant_call_sid)

        return {
            'data': {
                'message':'success'
            }
        }

class EndConferenceApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        conference_sid = input.get('conference_sid', None)
        
        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        twilio_helper.update_conference(conference_sid, {'status':'completed'})

        return {
            'data': {
                'message':'success'
            }
        }

class HoldCallApi(Resource):
    def post(self):
        input = request.get_json()
        call_sid = input.get('call_sid', None)
        conference_sid = input.get('conference_sid', None)
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        user_identity = input.get('user_identity', None)

        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        
        sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
        for sync_list_item in sync_list_items:
            sync_list_item_data = sync_list_item.data
            if sync_list_item_data['conference']['sid'] == conference_sid:
                sync_list_item_data['conference']['status'] = 'hold'

                twilio_helper.update_conference_participant(conference_sid, call_sid, {"end_conference_on_exit" : False})
                twilio_helper.update_call(call_sid, {"status":"completed"})
                twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index, {'data':sync_list_item_data})
                break

        return {
            'data': {
                'message':'success'
            }
        }
        
class ResumeCallApi(Resource):
    def post(self):
        input = request.get_json()
        source_call_sid = input.get('source_call_sid', None)
        call_sid = input.get('call_sid', None)
        conference_sid = input.get('conference_sid', None)
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        user_identity = input.get('user_identity', None)
        user_number = input.get('user_number', None)
        device_id = input.get('device_id', None)

        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        
        conference_callback_url = SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/conference/create-participant/status-callback' \
                            +'?source_call_sid='+urllib.parse.quote(source_call_sid) \
                            +'&tenant_id='+urllib.parse.quote(tenant_id) \
                            +'&subtenant_id='+urllib.parse.quote(subtenant_id) \
                            +'&user_identity='+urllib.parse.quote(user_identity) \
                            +'&conference_sid='+conference_sid

        max_call_and_ring_duration = AppHelper().get_max_call_and_ring_duration(tenant_id)
        conference_perticipant = twilio_helper.create_conference_participant(
            conference_sid, {
                'from_': user_number,
                'to': 'client:'+user_identity+'?auto_answer=true&device_id='+device_id,
                'early_media': False,
                'beep': 'onEnter',
                'end_conference_on_exit' : True,
                'status_callback': conference_callback_url,
                'status_callback_method': 'POST',
                'status_callback_event': ['answered', 'completed'],
                'timeout': max_call_and_ring_duration['ring'],
                'time_limit': max_call_and_ring_duration['call']
            })

        if conference_perticipant.call_sid:
            sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
            for sync_list_item in sync_list_items:
                sync_list_item_data = sync_list_item.data
                if sync_list_item_data['conference']['sid'] == conference_sid:
                    sync_list_item_data['conference']['status'] = 'in-progress'

                    participants = sync_list_item_data['conference']['participants']
                    for i, participant in enumerate(participants):
                        if participant['callSid'] == call_sid:
                            participant['callSid'] = conference_perticipant.call_sid
                            break

                    twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index, {'data':sync_list_item_data})
                    break

        return {
            'data': {
                'message':'success'
            }
        }
        
class StartWarmTransferApi(Resource):
    def post(self):
        input = request.get_json()
        conference_sid = input.get('conference_sid', None)
        call_sid = input.get('call_sid', None)
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        user_identity = input.get('user_identity', None)
        from_ = input.get('from_', None)
        to_number = input.get('to_number', None)
        to_name = input.get('to_name', None)

        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})

               
        source_call_sid = None
        sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
        for sync_list_item in sync_list_items:
            sync_list_item_data = sync_list_item.data
            if sync_list_item_data['conference']['sid'] == conference_sid:
                source_call_sid = sync_list_item_data['call']['sid']
                participants = sync_list_item_data['conference']['participants']
                for i, participant in enumerate(participants):
                    if participant['callSid'] != call_sid:
                        twilio_helper.update_conference_participant(conference_sid, participant['callSid'], {"hold" : True})
                break

        """
        Add new participant
        """
        conference_callback_url = SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/conference/create-participant/status-callback' \
            +'?source_call_sid='+urllib.parse.quote(source_call_sid) \
            +'&tenant_id='+urllib.parse.quote(tenant_id) \
            +'&subtenant_id='+urllib.parse.quote(subtenant_id) \
            +'&user_identity='+urllib.parse.quote(user_identity) \
            +'&conference_sid='+conference_sid

        max_call_and_ring_duration = AppHelper().get_max_call_and_ring_duration(tenant_id)
        conference_perticipant = twilio_helper.create_conference_participant(
            conference_sid, {
                'label': 'warm-transfer',
                'from_': from_,
                'to': to_number,
                'early_media': True,
                'beep': 'onEnter',
                'end_conference_on_exit' : False,
                'status_callback': conference_callback_url,
                'status_callback_method': 'POST',
                'status_callback_event': ['ringing', 'answered', 'completed'],
                'timeout': max_call_and_ring_duration['ring'],
                'time_limit': max_call_and_ring_duration['call']
            })

        new_participant = AppHelper().get_sync_list_call_obj_template()['conference']['participants'][0]
        new_participant['direction'] = 'outbound-api'
        new_participant['callSid'] = conference_perticipant.call_sid
        new_participant['name'] = to_name
        new_participant['to'] = to_number
        new_participant['from_'] = from_
        new_participant['startTime'] = str(datetime.utcnow())
        new_participant['callStatus'] = 'initiated'
        new_participant['type'] = 'warm-transfer'

        sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
        for sync_list_item in sync_list_items:
            sync_list_item_data = sync_list_item.data
            if sync_list_item_data['call']['sid'] == source_call_sid:
                sync_list_item_data['conference']['participants'].append(new_participant)
                sync_list_item_data['warmTransfer']['status'] = 'in-progress'
                twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index, {'data':sync_list_item_data})
                break

        return {
            'data': {
                'message':'success'
            }
        }
        
class CompleteWarmTransferApi(Resource):
    def post(self):
        input = request.get_json()
        conference_sid = input.get('conference_sid', None)
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        from_ = input.get('from_', None)
        to = input.get('to_number', None)
        call_sid = input.get('call_sid', None)
        
        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        
        sender_user_identity = AppHelper().get_user_identity(from_)
        receiver_user_identity = AppHelper().get_user_identity(to)  
        
        sender_sync_data = None
        sender_sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], sender_user_identity, {'limit':99})
        for sender_sync_list_item in sender_sync_list_items:
            sender_sync_list_item_data = sender_sync_list_item.data
            if sender_sync_list_item_data['conference']['sid'] == conference_sid:
                sender_sync_data = sender_sync_list_item.data
                break
          
        receiver_sync_data = None
        receiver_sync_index_to_update = None
        receiver_sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], receiver_user_identity, {'limit':99})
        for i, receiver_sync_list_item in enumerate(receiver_sync_list_items):
            receiver_sync_list_item_data = receiver_sync_list_item.data
            if receiver_sync_list_item_data['conference']['status'] == 'in-progress': #TODO: also validate "to" & "from" number in sync list item data.
                participants = receiver_sync_list_item_data['conference']['participants']
                for participant in participants:
                    if participant['from_'] == from_:
                        receiver_sync_index_to_update = i
                        receiver_sync_data = receiver_sync_list_item.data
                        break
                break
            
        """
        Update all source conference participant's end_conference_on_exit to false, to avaoid destination conference getting disconnected
        """
        sender_conference_participants = twilio_helper.list_conference_participants(conference_sid, {'limit':99})
        if sender_conference_participants:
            for sender_conference_participant in sender_conference_participants:
                twilio_helper.update_conference_participant(conference_sid, sender_conference_participant.call_sid, {"end_conference_on_exit" : 'false'})
                    
        receiver_conference_participants = twilio_helper.list_conference_participants(receiver_sync_data['conference']['sid'], {'limit':99})
        if receiver_conference_participants:
            for receiver_conference_participant in receiver_conference_participants:
                twilio_helper.update_conference_participant(receiver_sync_data['conference']['sid'], receiver_conference_participant.call_sid, {"end_conference_on_exit" : 'false'})
        
        receiver_conference_friendly_name = twilio_helper.fetch_conference(receiver_sync_data['conference']['sid']).friendly_name
        response = VoiceResponse()
        dial = Dial()
        dial.conference(receiver_conference_friendly_name)
        response.append(dial)

        participant_callback_url = SERVER_NAME + SERVER_APP_BASE_URL + '/api/call/conference/create-participant/status-callback' \
            +'?source_call_sid='+urllib.parse.quote(receiver_sync_data['call']['sid']) \
            +'&tenant_id='+urllib.parse.quote(tenant_id) \
            +'&subtenant_id='+urllib.parse.quote(subtenant_id) \
            +'&user_identity='+urllib.parse.quote(receiver_user_identity) \
            +'&conference_sid='+conference_sid

        participants = sender_sync_data['conference']['participants']
        for i, participant in enumerate(participants):
            if participant['callSid'] != call_sid and participant['type'] != 'warm-transfer':
                twilio_helper.update_call(participant['callSid'],
                    {
                        'status_callback': participant_callback_url,
                        'status_callback_method': 'POST',
                        'twiml':response
                    }
                )


        """
        Update destination sync list item data
        """
        if sender_sync_data['call']['direction'] == 'inbound':
            """
            Incoming
                Participant
                    Source
                        name = worker 1 source name
                        from_ = worker 1 source from_
                        callSid = worker 1 source call sid

                    Destination
                        callStaus = should be in-progress(Bug in existing code)
                        from_ = worker 1 destination from_
                    
                    copy remaining participant as it is excluding worker 2 where participant type = ''

                Call
                    sid = worker 1 call sid
            """
                
            source_data = dict()
            source_data['remaining_participants'] = list()
            participants = sender_sync_data['conference']['participants']
            for i, participant in enumerate(participants):
                if participant['type'] == 'source':
                    source_data['source'] = dict()
                    source_data['source']['name'] = participant['name']
                    source_data['source']['from_'] = participant['from_']
                    source_data['source']['call_sid'] = participant['callSid']
                    
                if participant['type'] == 'destination':
                    source_data['destination'] = dict()
                    source_data['destination']['from_'] = participant['from_']
                    
                if participant['type'] == '':
                    source_data['remaining_participants'].append(participant)
                    
            for i, participant in enumerate(receiver_sync_data['conference']['participants']):
                if participant['type'] == 'source':
                    participant['name'] = source_data['source']['name']
                    participant['from_'] = source_data['source']['from_']
                    participant['callSid'] = source_data['source']['call_sid']
                    
                    twilio_helper.update_conference_participant(receiver_sync_data['conference']['sid'], participant['callSid'], {"end_conference_on_exit" : 'true'})

                if participant['type'] == 'destination':
                    participant['from_'] = source_data['destination']['from_']
                    
                    twilio_helper.update_conference_participant(receiver_sync_data['conference']['sid'], participant['callSid'], {"end_conference_on_exit" : 'true'})

            for i, remaining_participant in enumerate(source_data['remaining_participants']):
                receiver_sync_data['conference']['participants'].append(remaining_participant)
            
            twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], receiver_user_identity, receiver_sync_index_to_update, {'data':receiver_sync_data})
        else:
            """
            Outgoing
                Participant
                    Copy existing source node from worker 2
                        direction = outbound-api
                        type = ''
                        to = worker 1 number
                        from_ = worker 2 number

                    Source 
                        to = ''
                        from_ = client:worker2

                    destination
                        direction = outbound-api
                        callSid = worker 1 destionation call sid
                        name = worker 1 destionation name
                        to = worker 1 destination node to
                        callStaus = should be in-progress(Bug in existing code)

                    copy remaining participant as it is excluding worker 2 where participant type = ''
                Call
                    direction - outbound-api
            """
            
            source_data = dict()
            source_data['remaining_participants'] = list()
            participants = sender_sync_data['conference']['participants']
            for i, participant in enumerate(participants):
                if participant['type'] == 'destination':                    
                    source_data['destination'] = participant

                if participant['type'] == '':
                    source_data['remaining_participants'].append(participant)
                    
            for i, participant in enumerate(receiver_sync_data['conference']['participants']):
                if participant['type'] == 'source':
                    del receiver_sync_data['conference']['participants'][i]

                if participant['type'] == 'destination':
                    participant['type'] = 'source'
                    
            receiver_sync_data['conference']['participants'].append(source_data['destination'])

            for i, remaining_participant in enumerate(source_data['remaining_participants']):
                receiver_sync_data['conference']['participants'].append(remaining_participant)
                
            receiver_sync_data['call']['direction'] = 'outbound-api'
            
            twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], receiver_user_identity, receiver_sync_index_to_update, {'data':receiver_sync_data})
            
            for i, participant in enumerate(receiver_sync_data['conference']['participants']):
                if participant['type'] in ('source', 'destination'):
                    twilio_helper.update_conference_participant(receiver_sync_data['conference']['sid'], participant['callSid'], {"end_conference_on_exit" : 'true'})
                    
        return {
            'data': {
                'message':'success'
            }
        }
        
class AbortWarmTrandferApi(Resource):
    def post(self):
        params = request.get_json()
        conference_sid = params.get('conference_sid', None)
        tenant_id = params.get('tenant_id', None)
        subtenant_id = params.get('subtenant_id', None)
        user_identity = params.get('user_identity', None)
        
        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        
        participants = twilio_helper.list_conference_participants(conference_sid, {'limit':99})
        if participants:
            for participant in participants:
                twilio_helper.update_conference_participant(conference_sid, participant.call_sid, {"hold" : False})
                if participant.label == 'warm-transfer':
                    twilio_helper.delete_conference_participant(conference_sid, participant.call_sid)
        
        time.sleep(5)
        
        sync_list_items = twilio_helper.get_sync_list_items(subaccount['sync_service_sid'], user_identity, {'limit':99})
        for sync_list_item in sync_list_items:
            sync_list_item_data = sync_list_item.data
            if sync_list_item_data['conference']['sid'] == conference_sid:
                participants = sync_list_item_data['conference']['participants']
                for i, participant in enumerate(participants):
                    if participant['type'] in ('source', 'destination'):
                        twilio_helper.update_conference_participant(conference_sid, participant['callSid'], {"end_conference_on_exit" : 'true'})

                sync_list_item_data['warmTransfer']['status'] = 'aborted'
                twilio_helper.update_sync_list_item(subaccount['sync_service_sid'], user_identity, sync_list_item.index, {'data':sync_list_item_data})
                break

        return {
            'data': {
                'message':'success'
            }
        }
        
        
        
        