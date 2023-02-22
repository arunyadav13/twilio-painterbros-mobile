import requests, json
from datetime import datetime
from models.phone_number import PhoneNumber, CallForwardingRule
from helpers.constants import Constants
from models.subaccount import SubAccount
from models.emergency_address import EmergencyAddress
from models.call import CallLog, Voicemail
from models.conversation import Conversation, ConversationParticipant, ConversationMessage
from models.us_city import UsCity
from models.contact import Contact
from models.settings import AccountSettings, SubaccountSettings
from helpers.twilio_helper import TwilioHelper
from config.constant import NCAMEO_API_BASE_URL, TEMP_LOCAL_TEST_CALL_FLOW

class DBHelper:
    
    def add_conversation(self, kwargs, tenant_id, subtenant_id):
        subaccount = self.get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        conversation = Conversation()
        conversation.subaccount_id = subaccount['id']
        conversation.twilio_sid = kwargs.get('ConversationSid')
        conversation.unique_name = kwargs.get('UniqueName')
        conversation.save()
        return conversation.as_dict()
    
    def get_conversation(self, kwargs):
        conversation = Conversation.query.filter_by(**kwargs).filter(Conversation.status!=Constants.Status.DELETED).first()
        if conversation:
            return conversation.as_dict()
        return
    
    def add_participant(self, kwargs, tenant_id, subtenant_id):
        number = kwargs.get('MessagingBinding.Address') if kwargs.get('MessagingBinding.Type') == 'sms' else '+' + kwargs.get('Identity')

        contact = self.get_contact(tenant_id, {'number': number})
        if not contact:
            contact = self.add_contact(tenant_id, { 'number': number })

        conversation = self.get_conversation({'twilio_sid': kwargs.get('ConversationSid')})
        participant = ConversationParticipant()
        participant.conversation_id = conversation['id']
        participant.twilio_sid = kwargs.get('ParticipantSid')
        participant.identity = kwargs.get('Identity')
        participant.type = kwargs.get('MessagingBinding.Type')
        participant.proxy_address = kwargs.get('MessagingBinding.ProxyAddress')
        participant.address = kwargs.get('MessagingBinding.Address')
        participant.contact_id = contact['id']
        participant.save()
        return participant.as_dict()
    
    def get_participant(self, kwargs):
        participant = ConversationParticipant.query.filter_by(**kwargs).filter(ConversationParticipant.status!=Constants.Status.DELETED).first()
        if participant:
            return participant.as_dict()
        return
    
    def delete_participant(self,  kwargs, tenant_id, subtenant_id):
        participant = ConversationParticipant.query.filter_by(ConversationParticipant.twilio_sid==kwargs.get('ParticipantSid')).filter(ConversationParticipant.status!=Constants.Status.DELETED).first()
        if participant:
            participant.status = Constants.Status.DELETED
            participant.deleted_at = datetime.utcnow()
            return participant.as_dict()
        return dict()
        
    def add_sms_log(self, kwargs, tenant_id, subtenant_id):
        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})

        conversation = self.get_conversation({'twilio_sid': kwargs.get('ConversationSid')})
        if not conversation:
            conversation_twilio = twilio_helper.fetch_conversation(subaccount['conversation_service_sid'], kwargs.get('ConversationSid'))
            conversation = self.add_conversation({
                'ConversationSid': conversation_twilio.sid, 
                'UniqueName': conversation_twilio.unique_name
            }, tenant_id, subtenant_id)

        participant = self.get_participant({'twilio_sid': kwargs.get('ParticipantSid')})
        if not participant:
            participant_twilio = twilio_helper.fetch_conversation_participant(subaccount['conversation_service_sid'], kwargs.get('ConversationSid'), kwargs.get('ParticipantSid'))
            participant = self.add_participant({
                'ConversationSid': kwargs.get('ConversationSid'),
                'ParticipantSid': participant_twilio.sid,
                'Identity': participant_twilio.identity,
                'MessagingBinding.Type': participant_twilio.messaging_binding.get('type') if participant_twilio.messaging_binding else None,
                'MessagingBinding.ProxyAddress': participant_twilio.messaging_binding.get('proxy_address') if participant_twilio.messaging_binding else None,
                'MessagingBinding.Address': participant_twilio.messaging_binding.get('address') if participant_twilio.messaging_binding else None
            }, tenant_id, subtenant_id)

        message = ConversationMessage()
        message.conversation_id = conversation['id']
        message.participant_id = participant['id']
        message.twilio_sid = kwargs.get('MessageSid')
        message.body = kwargs.get('Body')
        message.media = kwargs.get('Media')
        message.save()

        conversation_message_count = ConversationMessage.query.filter(ConversationMessage.conversation_id==conversation['id'], ConversationMessage.status!=Constants.Status.DELETED).count()
        if conversation_message_count == 1:
            sms_participant = self.get_participant({'conversation_id': conversation['id'], 'type': 'sms'})
            if sms_participant:
                body = 'Welcome to Painter Bros! You are now receiving text message communications. If you\'d like to stop receiving messages at any time, please reply with STOP'
                twilio_helper.send_message({'from_': sms_participant['proxy_address'], 'body': body, 'to': sms_participant['address']})
            
        body = kwargs.get('Body', '').lower().strip()
        if kwargs.get('Source', '').lower() == 'sms' and body in ['stop', 'start']:
            contact = Contact.query.filter(Contact.tenant_id == tenant_id, Contact.number == kwargs.get('Author'), Contact.status!=Constants.Status.DELETED).first()
            contact.sms_consent = True if body == 'start' else False
            contact.save()
            
        conversation_participants = twilio_helper.list_conversation_participants(subaccount['conversation_service_sid'], kwargs.get('ConversationSid'), {'limit': 99})
        for cp in conversation_participants:
            if cp.identity and cp.identity != kwargs.get('Author'):
                payload = json.dumps({"parameters": {}, "payload": {
                    "FromNumber": kwargs.get('Author'),
                    "ToNumber": cp.identity,
                    "DateSent": datetime.strptime(kwargs.get('DateCreated'), '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y-%m-%d %H:%M:%S"),
                    "Body": kwargs.get('Body'),
                    "MessageSid": kwargs.get('MessageSid'),
                    "Status": 'queued' if kwargs.get('Author') == cp.identity else 'received',
                    "Direction": 'outbound-api' if kwargs.get('Author') == cp.identity else 'inbound',
                    "ConversationSid": kwargs.get('ConversationSid')
                }})
                headers = {
                    'Content-Type': 'application/json'
                }
                requests.request("POST", NCAMEO_API_BASE_URL + "/twilio/twilioinsertsmslog", headers=headers, data=payload).json()
        return 'success'
    
    def on_delivery_updated(self, kwargs, tenant_id, subtenant_id):
        twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id}) 
        subaccount = self.get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        conversation_message = twilio_helper.fetch_conversation_message(subaccount['conversation_service_sid'], kwargs.get('ConversationSid'), kwargs.get('MessageSid'))
        conversation_message_detailed_delivery_receipts_json = []
        conversation_message_detailed_delivery_receipts = twilio_helper.fetch_conversation_message_detailed_delivery_receipts(subaccount['conversation_service_sid'], kwargs.get('ConversationSid'), kwargs.get('MessageSid'))
        for record in conversation_message_detailed_delivery_receipts:
            conversation_message_detailed_delivery_receipts_json.append({
                "sid": record.sid,
                "status": record.status,
                "error_code": record.error_code,
                "participant_sid": record.participant_sid,
                "date_created": str(record.date_created),
                "date_updated": str(record.date_updated),
            })
        self.update_conversation_message(kwargs.get('MessageSid'), {'delivery': conversation_message.delivery, 'delivery_receipts': conversation_message_detailed_delivery_receipts_json})
        self.update_sms_log(kwargs)
        
    def update_sms_log(self, kwargs):
        payload = json.dumps({"parameters": {
            "Status": kwargs.get('Status'),
            "MessageSid": kwargs.get('MessageSid')
        }})
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", NCAMEO_API_BASE_URL + "/twilio/twilioupdatesmslog", headers=headers, data=payload).json()
        return 'success'
        
    def update_call_log(self, kwargs):
        payload = json.dumps({"parameters": {
            "CallSid": kwargs.get('call_sid'),
            "VoicemailUrl": kwargs.get('voicemail_url'),
            "Status": kwargs.get('status')
        }})
        headers = {
            'Content-Type': 'application/json'
        }
        requests.request("POST", NCAMEO_API_BASE_URL + "/twilio/twilioupdatecalllog", headers=headers, data=payload).json()
        return 'success'

    def get_consolidated_call_log(self, conference_sid):
        call_logs = CallLog.query.filter(CallLog.conference_sid==conference_sid, CallLog.status!=Constants.Status.DELETED).order_by(CallLog.id.asc())
        row_count = call_logs.count()
        call_logs = call_logs.all()
        i = 0
        first_row = None
        last_row = None
        row = None
        for call_log in call_logs:
            i = i + 1
            if i == 1:
                first_row = call_log
            if row_count == i:
                last_row = call_log
            if call_log.source_number != call_log.destination_number:
                row = call_log
        if row:
            row.call_duration =  int(last_row.timestamp.timestamp() - (first_row.timestamp.timestamp() - (first_row.call_duration if first_row.call_duration else 0)))
            return row.as_dict()
        return
    
    def get_call_sids_by_source_call_sid(self, source_call_sid):
        results = list()
        call_logs = CallLog.query.filter(CallLog.source_call_sid==source_call_sid, CallLog.status!=Constants.Status.DELETED).all()
        if call_logs:
            for call_log in call_logs:
                results.append(call_log.call_sid)
        return results
    
    def get_call_logs(self, kwargs):
        call_logs = CallLog.query.filter_by(**kwargs).filter(CallLog.status!=Constants.Status.DELETED).all()
        result = list()
        if call_logs:
            for call_log in call_logs:
                result.append(call_log.as_dict())
        return result
    
    def get_call_log(self, kwargs):
        call_log = CallLog.query.filter_by(**kwargs).filter(CallLog.status!=Constants.Status.DELETED).first()
        if call_log:
            return call_log.as_dict()
        return
    
    def save_call_log(self, subaccount, kwargs, direction, conference_sid, source_call_sid=None):
        call_log = CallLog.query.filter(CallLog.status!=Constants.Status.DELETED, CallLog.call_sid==kwargs.get('CallSid'), CallLog.conference_sid==conference_sid).first()
        if not call_log:
            call_log = CallLog()
            call_log.subaccount_id = subaccount['id']
            call_log.conference_sid = conference_sid
            call_log.call_sid = kwargs.get('CallSid')
            call_log.source_call_sid = source_call_sid
        call_log.call_duration = kwargs.get('CallDuration')
        call_log.source_number = kwargs.get('From')
        source_contact = self.search_contact(subaccount['tenant_id'], call_log.source_number[-10:])
        if source_contact:
            call_log.source_name =source_contact[0]['name']
        source_phone_number = self.get_phone_number(call_log.source_number)
        if source_phone_number:
            call_log.source_phone_number_id = source_phone_number['id']
        call_log.destination_number = kwargs.get('To').replace('client:', '+').replace('sip:', '+')
        destination_contact = self.search_contact(subaccount['tenant_id'], call_log.destination_number[-10:])
        if destination_contact:
            call_log.destination_name =destination_contact[0]['name']
        destination_phone_number = self.get_phone_number(call_log.destination_number)
        if destination_phone_number:
            call_log.destination_phone_number_id = destination_phone_number['id']
        call_log.call_status = kwargs.get('CallStatus')
        call_log.timestamp = datetime.strptime(kwargs.get('Timestamp'), '%a, %d %b %Y %H:%M:%S +0000')
        call_log.direction = direction
        call_log.log_for_user_id = ' '
        call_log.save()
        if destination_phone_number:
            voicemail = Voicemail.query.filter(Voicemail.call_sid==call_log.source_call_sid, Voicemail.phone_number_id==destination_phone_number['id']).filter(Voicemail.status!=Constants.Status.DELETED).first()
            if voicemail:
                voicemail.call_log_id = call_log.id
                voicemail.save()
        return 'success'

    def get_contact(self, tenant_id, kwargs):
        contact = Contact.query.filter_by(**kwargs).filter(Contact.tenant_id==tenant_id, Contact.status!=Constants.Status.DELETED).first()
        if contact:
            return contact.as_dict()
        return dict()

    def add_contact(self, tenant_id, kwargs):
        new_contact = Contact()
        new_contact.tenant_id = tenant_id
        new_contact.number = kwargs.get('number')
        search_contact_response = self.search_contact(tenant_id, kwargs.get('number'))
        if search_contact_response:
            new_contact.name = search_contact_response[0]['name']
            new_contact.type = search_contact_response[0]['type']
        new_contact.save()
        return new_contact.as_dict()

    def search_contact(self, tenant_id, search_query, kwargs = dict()):
        user_number = '+' + kwargs.get('user_identity') if kwargs.get('user_identity') else ''
        payload = json.dumps({
            "parameters": {
                "Tenant_Id": tenant_id,
                "FranchiseId": kwargs.get('subtenant_id') if kwargs.get('subtenant_id') else '',
                "SearchParam": search_query,
                "UserNumber": user_number,
                # "GetAllRecords": False if user_number else True, # TODO: uncomment it to enable restricted contact search as per client's requirement after QA.
                "GetAllRecords": True,
            },
            "payload": {}
        })

        headers = {
            'Content-Type': 'application/json'
        }

        search_contact_response = list()
        response = requests.request("GET", NCAMEO_API_BASE_URL + "/twilio/twiliocontactsearch", headers=headers, data=payload).json()
        if response.get('data') and len(response['data']) >= 1:
            for contact in response['data']:
                """
                ETL logic
                """
                ct = dict()
                ct['name'] = contact['Name']
                ct['type'] = contact['Type']
                ct['numbers'] = list()
                for num_type in contact['Numbers'][0]:
                    if contact['Numbers'][0][num_type]:
                        number = dict()
                        number['number'] = contact['Numbers'][0][num_type]
                        number['type'] = num_type.lower()
                        ct['numbers'].append(number)
                if len(ct['numbers']) > 0:
                    search_contact_response.append(ct)
        return search_contact_response

    def get_phone_number(self, number):
        # TODO: implement kwargs based search also use "tenant_id" and/or "subtenant_id" filter or "subaccount_id" filter while getting the phone number.
        # TODO: handle if same number has been purchsed by different tenant at different times
        phone_number = PhoneNumber.query.filter(PhoneNumber.status!=-1, PhoneNumber.number==number).first()
        if phone_number:
            return phone_number.as_dict()
        return dict()
    
    def add_phone_number(self, subaccount_id, api_response):
        phone_number = PhoneNumber()
        phone_number.subaccount_id = subaccount_id
        phone_number.number = api_response.phone_number
        phone_number.twilio_sid = api_response.sid
        phone_number.save()
        return phone_number.as_dict()
    
    def delete_phone_number(self, twilio_sid):
        phone_number = PhoneNumber.query.filter(PhoneNumber.status!=-1, PhoneNumber.twilio_sid==twilio_sid).first()
        phone_number.status = -1
        phone_number.deleted_at = datetime.utcnow()
        phone_number.save()
        return phone_number.as_dict()
    
    def add_subaccount(self, tenant_id, subtenant_id, api_response):
        subaccount = SubAccount()
        subaccount.tenant_id = tenant_id
        subaccount.subtenant_id = subtenant_id
        subaccount.account_sid = api_response.sid
        subaccount.auth_token = api_response.auth_token
        subaccount.account_status = api_response.status
        subaccount.save()
        return subaccount.as_dict()
    
    def get_subaccount(self, kwargs):
        subaccount = SubAccount.query.filter_by(**kwargs).filter(SubAccount.status!=-1).first()
        if subaccount:
            return subaccount.as_dict()
        return
    
    def get_subaccounts(self, kwargs):
        subaccounts = SubAccount.query.filter_by(**kwargs).filter(SubAccount.status!=-1).first()
        result = list()
        if subaccounts:
            for subaccount in subaccounts:
                result.append(subaccount.as_dict())
        return result

    def get_account_settings(self, tenant_id, name):
        account_settings = AccountSettings.query.filter(AccountSettings.tenant_id==tenant_id, AccountSettings.name==name, AccountSettings.status!=Constants.Status.DELETED).first()
        if account_settings:
            return account_settings.as_dict()
        return dict()

    def get_subaccount_settings(self, subaccount_id, name):
        subaccount_settings = SubaccountSettings.query.filter(SubaccountSettings.tenant_id==subaccount_id, SubaccountSettings.name==name, SubaccountSettings.status!=Constants.Status.DELETED).first()
        if subaccount_settings:
            return subaccount_settings.as_dict()
        return dict()
    
    def get_call_forwarding_rules(self, kwargs):
        call_forwarding_rules = CallForwardingRule.query.filter_by(**kwargs).filter(CallForwardingRule.status==Constants.Status.ACTIVE.value).all()
        call_forwarding_rules_list = list()
        for call_forwarding_rule in call_forwarding_rules:
            call_forwarding_rules_list.append(call_forwarding_rule.as_dict())
        return call_forwarding_rules_list

    def add_call_forwarding_rule(self, kwargs):
        call_forwarding_rule = CallForwardingRule()
        call_forwarding_rule.phone_number_id = kwargs.get('phone_number_id')
        call_forwarding_rule.number = kwargs.get('number')
        call_forwarding_rule.number_type = kwargs.get('number_type')
        call_forwarding_rule.duration = kwargs.get('duration')
        call_forwarding_rule.save()
        return call_forwarding_rule.as_dict()

    def delete_call_forwarding_rule(self, rule_id):
        call_forwarding_rule = CallForwardingRule.query.filter(CallForwardingRule.status!=-1, CallForwardingRule.id==rule_id).first()
        if call_forwarding_rule:
            call_forwarding_rule.status = Constants.Status.DELETED.value
            call_forwarding_rule.deleted_at = datetime.utcnow()
            call_forwarding_rule.save()
            return call_forwarding_rule.as_dict()
        return dict()

    def restore_call_forwarding_rule(self, rule_id):
        call_forwarding_rule = CallForwardingRule.query.filter(CallForwardingRule.status==-1, CallForwardingRule.id==rule_id).first()
        if call_forwarding_rule:
            call_forwarding_rule.status = Constants.Status.ACTIVE.value
            call_forwarding_rule.deleted_at = '0001-01-01 00:00:00'
            call_forwarding_rule.save()
            return call_forwarding_rule.as_dict()
        return dict()

    def get_pre_lead_or_lead_by_phone_number(self, phone_number):
        payload = json.dumps({"parameters": {"From_": phone_number}, "payload":{}})
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", NCAMEO_API_BASE_URL + "/twilio/twiliopreleadorleadbyphone", headers=headers, data=payload).json()
        if response.get('data') and len(response['data']) >= 1:
            return response['data'][0]
        return
    
    def get_lead_by_phone_number(self, number):
        api_response = {
            "data": [
                {
                    "Address": "826 E State St, American Fork, UT 84003, USA",
                    "CustomerId": "c12ac060-df52-49cc-bc1c-f520e411004c",
                    "Email": "testdiscard@mailinator.com",
                    "FirstName": "Test ",
                    "LastName": "Discard",
                    "Mobile": "+18888888888",
                    "Organization": None,
                    "Phone": None,
                    "ZipCode": 84003,
                    "CallFlow": TEMP_LOCAL_TEST_CALL_FLOW
                }
            ],
            "message": None,
            "statusCode": 201,
            "__lastupdateddate": None,
            "__lastupdatedby": None
        }
        
        lead = dict()
        lead['call_flow'] = dict()
        lead['call_flow']['targets'] = list()
        for target in api_response['data'][0]['CallFlow']['Targets']:
            if target['Number'] and target['Number'] != '':
                call_flow_target = dict()
                call_flow_target['name'] = target['Name']
                call_flow_target['number'] = target['Number']
                lead['call_flow']['targets'].append(call_flow_target)
        
        if api_response['data'][0]['CallFlow']['Voicemail'] and api_response['data'][0]['CallFlow']['Voicemail']['Number'] and api_response['data'][0]['CallFlow']['Voicemail']['Number'] != '':
            voicemail_target = dict()
            voicemail_target['name'] = api_response['data'][0]['CallFlow']['Voicemail']['Name']
            voicemail_target['number'] = api_response['data'][0]['CallFlow']['Voicemail']['Number']
            lead['call_flow']['voicemail'] = voicemail_target
        
        return lead
    
    
    def edit_subaccount(self, twilio_sid, kwargs):
        subaccount = SubAccount.query.filter(SubAccount.status!=-1, SubAccount.account_sid==twilio_sid).first()
        subaccount.messaging_service_sid = kwargs.get('messaging_service_sid')
        subaccount.twiml_app_sid = kwargs.get('twiml_app_sid')
        subaccount.sync_service_sid = kwargs.get('sync_service_sid')
        subaccount.call_logs_sync_service_sid = kwargs.get('call_logs_sync_service_sid')
        subaccount.api_key = kwargs.get('api_key')
        subaccount.api_secret = kwargs.get('api_secret')
        subaccount.conversation_service_sid = kwargs.get('conversation_service_sid')
        subaccount.a2p_10dlc_campaign_sid = kwargs.get('a2p_10dlc_campaign_sid')
        subaccount.ivr_flow_sid = kwargs.get('ivr_flow_sid')
        subaccount.save()
        return subaccount.as_dict()
    
    def delete_subaccount(self, twilio_sid):
        subaccount = SubAccount.query.filter(SubAccount.status!=-1, SubAccount.account_sid==twilio_sid).first()
        subaccount.status = -1
        subaccount.deleted_at = datetime.utcnow()
        subaccount.save()
        return 'success'

    def get_emergency_address(self, kwargs):
        emergency_address = EmergencyAddress.query.filter_by(**kwargs).filter(EmergencyAddress.status!=-1).first()
        if emergency_address:
            return emergency_address.as_dict()
        return
    
    def add_emergency_address(self, subaccount_id, api_response):
        emergency_address = EmergencyAddress()
        emergency_address.subaccount_id = subaccount_id
        emergency_address.twilio_sid = api_response.sid
        emergency_address.customer_name = api_response.customer_name
        emergency_address.street = api_response.street
        emergency_address.city = api_response.city
        emergency_address.region = api_response.region
        emergency_address.postal_code = api_response.postal_code
        emergency_address.iso_country = api_response.iso_country
        emergency_address.save()
        return emergency_address.as_dict()

    def get_sms_conversations_list(self, kwargs):
        conversation_params = kwargs.get('conversation', dict())
        participant_params = kwargs.get('participant', dict())

        conversation_objs = Conversation.query \
            .filter_by(**conversation_params) \
            .join(ConversationParticipant).filter_by(**participant_params) \
            .filter(Conversation.status!=Constants.Status.DELETED, ConversationParticipant.status!=Constants.Status.DELETED) \
            .all()

        conversations = list()
        for conversation_obj in conversation_objs:
            conversations.append(conversation_obj.as_dict())
        return conversations

    def get_sms_list(self, conversation_sid):
        payload = json.dumps({"parameters": { "ConversationSid": conversation_sid }, "payload": {}})
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", NCAMEO_API_BASE_URL + "/twilio/twiliogetsmsbyconversationsid", headers=headers, data=payload).json()
        if response and response.get('data') and len(response.get('data')) >= 1:
            return response['data']
        return list()
    
    def update_conversation_message(self, twilio_sid, kwargs):
        conversation_message = ConversationMessage.query.filter(ConversationMessage.status!=Constants.Status.DELETED, ConversationMessage.twilio_sid==twilio_sid).first()
        if conversation_message:
            if kwargs.get('delivery'):
                conversation_message.delivery = kwargs.get('delivery')
            if kwargs.get('delivery_receipts'):
                conversation_message.delivery_receipts = kwargs.get('delivery_receipts')
            conversation_message.save()
            return conversation_message.as_dict()
        return
    
    def get_messages_list(self, conversation_sid):
        messages = ConversationMessage.query.join(ConversationMessage.participant).join(ConversationParticipant.conversation).filter(ConversationMessage.status!=Constants.Status.DELETED, Conversation.twilio_sid==conversation_sid).all()
        result = list()
        if messages:
            for message in messages:
                result.append(message.as_dict())
        return result

    def get_us_city_by_zipcode(self, zip_code):
        search = "%{}%".format(zip_code)
        us_city = UsCity.query.filter(UsCity.zips.like(search)).first()
        if us_city:
            return us_city.as_dict()
        return
    
    def get_subtenant_by_zipcode(self, zipcode):
        payload = json.dumps({"parameters": { "ZipCode": zipcode}})
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", NCAMEO_API_BASE_URL + "/twilio/twiliofranchisebyzip", headers=headers, data=payload).json()
        if response.get('data') and len(response['data']) >= 1:
            return response['data'][0]
        return
    
    def save_voicemail(self, kwargs, phone_number=None, voicemail_path=None):
        voicemail = Voicemail.query.filter(Voicemail.twilio_sid==kwargs.get('RecordingSid')).filter(Voicemail.status!=Constants.Status.DELETED).first()
        if not voicemail and kwargs.get('CallSid'):
            voicemail = Voicemail()
            voicemail.twilio_sid = kwargs.get('RecordingSid')
            voicemail.call_sid = kwargs.get('CallSid')
            if kwargs.get('RecordingStartTime'):
                voicemail.recording_start_at = datetime.strptime(kwargs.get('RecordingStartTime'), '%a, %d %b %Y %H:%M:%S +0000')
            voicemail.duration = kwargs.get('RecordingDuration')
            voicemail.recording_status = kwargs.get('RecordingStatus')
        if voicemail_path:
            voicemail.s3_path = voicemail_path
        voicemail.transcribed_text = kwargs.get('TranscriptionText')
        if phone_number:
            phone_number_details = self.get_phone_number(phone_number)
            if phone_number_details:
                voicemail.phone_number_id = phone_number_details['id']
            call_log = self.get_call_log({'source_call_sid': kwargs.get('CallSid'), 'destination_number': phone_number})
            if call_log:
                voicemail.call_log_id = call_log['id']
        voicemail.save()
        return 'success'

    def get_voicemail(self, kwargs):
        voicemail = Voicemail.query.filter_by(**kwargs).filter(Voicemail.status!=Constants.Status.DELETED).first()
        if voicemail:
            return voicemail.as_dict()
        return
        
    def create_prelead(self, phone_number, zip_code):
        payload = json.dumps({
            "parameters":{},
            "payload":{
            "Phone":phone_number,
            "ZipCode":zip_code
            }})
        headers = {
            'Content-Type': 'application/json'
        }
        requests.request("POST", NCAMEO_API_BASE_URL + "/twilio/createprelead", headers=headers, data=payload).json()
        return 'success'
