import os
from requests import Request, Session
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient
from twilio.http.response import Response
from models.subaccount import SubAccount

class TwilioHelper:

    def __init__(self, kwargs):
        self.twilio_client = self.init_twilio_client(kwargs)

    # Twilio Client
    def init_twilio_client(self, kwargs):
        if kwargs.get('account_sid') and kwargs.get('auth_token'):
            twilio_client = Client(kwargs.get('account_sid'), kwargs.get('auth_token'), http_client=kwargs.get('http_client', None))
            return twilio_client
        elif kwargs.get('tenant_id') and kwargs.get('subtenant_id'):
            subaccount = SubAccount.query.filter_by(status = True, tenant_id=kwargs.get('tenant_id'), subtenant_id=kwargs.get('subtenant_id')).first()
            if not subaccount:
                raise Exception('Sub account does not exist')
            twilio_client = Client(subaccount.account_sid, subaccount.auth_token)
            return twilio_client
        raise Exception('Invalid kwargs')

    def get_twilio_client(self):
        return self.twilio_client

    # Call
    def create_call(self, kwargs):
        api_response = self.twilio_client.calls.create(**kwargs)
        return api_response

    # Conference
    def create_conference_participant(self, conference_sid, kwargs):
        api_response = self.twilio_client.conferences(conference_sid) \
            .participants \
            .create(**kwargs)
        return api_response

    def update_conference_participant(self, conference_sid, participant_sid, kwargs):
        api_response =  self.twilio_client.conferences(conference_sid) \
            .participants(participant_sid) \
            .update(**kwargs)
        return api_response

    def delete_conference_participant(self, conference_sid, participant_sid):
        api_response =  self.twilio_client.conferences(conference_sid) \
            .participants(participant_sid) \
            .delete()
        return api_response

    def update_conference(self, conference_sid, conference_attr):
        api_response =  self.twilio_client.conferences(conference_sid) \
            .update(**conference_attr)
        return api_response

    def fetch_conference(self, conference_sid):
        api_response = self.twilio_client.conferences(conference_sid) \
            .fetch()
        return api_response
    
    def list_conference_participants(self, conference_sid, kwargs):
        api_response = self.twilio_client.conferences(conference_sid) \
            .participants.list(**kwargs)
        return api_response

    # Sync
    def create_sync_service(self, kwargs):
        api_response = self.twilio_client.sync.v1.services.create(**kwargs)
        return api_response

    def create_sync_service(self, kwargs):
        api_response = self.twilio_client.sync.v1.services.create(**kwargs)
        return api_response

    def fetch_sync_service(self, sync_service_sid):
        api_response = self.twilio_client.sync.v1.services(sync_service_sid).fetch()
        return api_response

    def read_sync_service(self, kwargs):
        api_response = self.twilio_client.sync.v1.services.list(**kwargs)
        return api_response

    def list_sync_lists(self, sync_service_sid, kwargs):
        api_response = self.twilio_client.sync.v1 \
                        .services(sync_service_sid) \
                        .sync_lists \
                        .list(**kwargs)
        return api_response

    def create_sync_list(self, sync_service_sid, kwargs):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .sync_lists \
            .create(**kwargs)
        return api_response
    
    def fetch_sync_list(self, sync_service_sid, sync_list_name):
        api_response = self.twilio_client.sync.v1 \
                .services(sync_service_sid) \
                .sync_lists(sync_list_name) \
                .fetch()
        return api_response

    def delete_sync_list(self, sync_service_sid, sync_list_sid_or_unique_name):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .sync_lists(sync_list_sid_or_unique_name) \
            .delete()
        return api_response

    def get_sync_list_items(self, sync_service_sid, sync_list_sid_or_unique_name, kwargs):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .sync_lists(sync_list_sid_or_unique_name) \
            .sync_list_items \
            .list(**kwargs)
        return api_response

    def create_sync_list_item(self, sync_service_sid, sync_list_sid_or_unique_name, kwargs):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .sync_lists(sync_list_sid_or_unique_name) \
            .sync_list_items \
            .create(**kwargs)
        return api_response

    def update_sync_list_item(self, sync_service_sid, sync_list_sid_or_unique_name, sync_list_item_index, kwargs):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .sync_lists(sync_list_sid_or_unique_name) \
            .sync_list_items(sync_list_item_index) \
            .update(**kwargs)
        return api_response

    def delete_sync_list_item(self, sync_service_sid, sync_list_sid_or_unique_name, sync_list_item_index):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .sync_lists(sync_list_sid_or_unique_name) \
            .sync_list_items(sync_list_item_index) \
            .delete()
        return api_response

    # Subaccount
    def create_subaccount(self, kwargs):
        return self.twilio_client.api.v2010.accounts.create(**kwargs)
        
    def fetch_subaccount(self, subaccount_sid):
        return self.twilio_client.api.v2010.accounts(subaccount_sid).fetch()

    def update_subaccount(self, subaccount_sid, kwargs):
        api_response =  self.twilio_client.api.v2010 \
                    .accounts(subaccount_sid) \
                    .update(**kwargs)
        return api_response
        
    def list_subaccounts(self, kwargs):
        return self.twilio_client.api.v2010.accounts.list(**kwargs)
    
    def search_available_local_phone_numbers(self, kwargs, country='US'):
        return self.twilio_client.available_phone_numbers(country).local.list(**kwargs)

    def create_emergency_address(self, kwargs):
        return self.twilio_client.addresses.create(**kwargs)

    def read_emergency_addresses(self, kwargs):
        return self.twilio_client.addresses.list(**kwargs)

    def fetch_emergency_addresses(self, emergency_address_sid):
        return self.twilio_client.addresses(emergency_address_sid).fetch()

    def update_emergency_address(self, emergency_address_sid, kwargs):
        return self.twilio_client.addresses(emergency_address_sid).update(**kwargs)
    
    def buy_phone_number(self, kwargs):
        return self.twilio_client.incoming_phone_numbers.create(**kwargs)

    def update_phone_number(self, incoming_phone_number_sid, kwargs):
        api_response =  self.twilio_client.incoming_phone_numbers(incoming_phone_number_sid) \
                        .update(**kwargs)
        return api_response

    def fetch_phone_number(self, incoming_phone_number_sid):
        api_response =  self.twilio_client.incoming_phone_numbers(incoming_phone_number_sid) \
                        .fetch()
        return api_response

    def create_twiml_app(self, kwargs):
        api_response = self.twilio_client.applications \
                    .create(**kwargs)
        return api_response

    def fetch_twiml_app(self, twiml_app_sid):
        api_response = self.twilio_client.applications(twiml_app_sid).fetch()
        return api_response

    def list_twiml_apps(self, kwargs):
        api_response = self.twilio_client.applications.list(**kwargs)
        return api_response

    def delete_phone_number(self, phone_number_sid):
        api_response =  self.twilio_client.incoming_phone_numbers(phone_number_sid).delete()
        return api_response
    
    def fetch_conversation_service(self, conversation_service_sid):
        api_response = self.twilio_client.conversations.v1 \
                     .services(conversation_service_sid) \
                     .fetch()
        return api_response
    
    def create_conversation_service(self, kwargs):
        api_response = self.twilio_client.conversations.v1 \
            .services \
            .create(**kwargs)
        return api_response

    def list_conversation_services(self, kwargs):
        api_response = self.twilio_client.conversations.v1 \
            .services \
            .list(**kwargs)
        return api_response

    def update_conversation_webhook(self, kwargs):
        api_response = self.twilio_client.conversations.v1 \
            .configuration \
            .webhooks() \
            .update(**kwargs)
        return api_response
    
    def create_conversation(self, conversation_service_sid, kwargs):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations \
                        .create(**kwargs)
        return api_response
    
    def fetch_conversation(self, conversation_service_sid, conversation_sid):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations(conversation_sid) \
                        .fetch()
        return api_response
    
    def delete_conversation(self, conversation_service_sid, conversation_sid):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations(conversation_sid) \
                        .delete()
        return api_response
    
    def list_conversations(self, conversation_service_sid, kwargs):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations \
                        .list(**kwargs)
        return api_response
    
    def list_conversation_participants(self, conversation_service_sid, conversation_sid, kwargs):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations(conversation_sid) \
                        .participants \
                        .list(**kwargs)
        return api_response
    
    def create_conversation_participant(self, conversation_service_sid, conversation_sid, kwargs):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations(conversation_sid) \
                        .participants \
                        .create(**kwargs)
        return api_response
    
    def fetch_conversation_participant(self, conversation_service_sid, conversation_sid, participant_sid):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations(conversation_sid) \
                        .participants(participant_sid) \
                        .fetch()
        return api_response
    
    def create_conversation_message(self, conversation_service_sid, conversation_sid, kwargs):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations(conversation_sid) \
                        .messages \
                        .create(**kwargs)
        return api_response
    
    def fetch_conversation_message(self, conversation_service_sid, conversation_sid, message_sid):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations(conversation_sid) \
                        .messages(message_sid) \
                        .fetch()
        return api_response

    def fetch_conversation_message_detailed_delivery_receipts(self, conversation_service_sid, conversation_sid, message_sid, kwargs=dict()):
        api_response = self.twilio_client.conversations \
                        .v1 \
                        .services(conversation_service_sid) \
                        .conversations(conversation_sid) \
                        .messages(message_sid) \
                        .delivery_receipts \
                        .list(**kwargs)
        return api_response
    
    def list_conversation_messages(self, conversation_service_sid, conversation_sid, kwargs):
        api_response = self.twilio_client.conversations.v1 \
                        .services(conversation_service_sid) \
                        .conversations(conversation_sid) \
                        .messages \
                        .list(**kwargs)
        return api_response

    def create_api_key(self, kwargs):
        api_response = self.twilio_client.new_keys.create(**kwargs)
        return api_response

    def fetch_api_key(self, api_key_sid):
        api_response = self.twilio_client.keys(api_key_sid).fetch()
        return api_response

    def delete_api_key(self, api_key_sid):
        api_response = self.twilio_client.keys(api_key_sid).delete()
        return api_response

    def read_api_keys(self, kwargs):
        api_response = self.twilio_client.keys.list(**kwargs)
        return api_response
        
    def send_message(self, kwargs):
        return self.twilio_client.messages.create(**kwargs)

    def create_messaging_service(self, kwargs):
        api_response = self.twilio_client.messaging.v1.services.create(**kwargs)
        return api_response

    def fetch_messaging_service(self, messaging_servie_sid):
        api_response = self.twilio_client.messaging.v1 \
                .services(messaging_servie_sid) \
                .fetch()
        return api_response

    def list_messaging_services(self, kwargs):
        api_response = self.twilio_client.messaging.v1.services.list(**kwargs)
        return api_response
    
    def add_phone_number_to_messaging_service(self, messaging_service_sid, kwargs):
        api_response = self.twilio_client.messaging.v1 \
                     .services(messaging_service_sid) \
                     .phone_numbers \
                     .create(**kwargs)
        return api_response

    def create_campaign(self, messaging_servie_sid, kwargs):
        api_response = self.twilio_client.messaging.v1 \
            .services(messaging_servie_sid) \
            .us_app_to_person \
            .create(**kwargs)
        return api_response

    def fetch_campaign(self, messaging_servie_sid, campaign_sid):
        api_response = self.twilio_client.messaging.v1 \
        .services(messaging_servie_sid) \
        .us_app_to_person(campaign_sid) \
        .fetch()
        return api_response

    def list_campaigns(self, messaging_servie_sid, kwargs):
        api_response = self.twilio_client.messaging.v1 \
        .services(messaging_servie_sid) \
        .us_app_to_person \
        .list(**kwargs)
        return api_response

    def update_call(self, call_sid, kwargs):
        api_response = self.twilio_client.calls(call_sid).update(**kwargs)
        return api_response

    def list_sync_documents(self, sync_service_sid, kwargs):
        api_response = self.twilio_client.sync \
                        .v1 \
                        .services(sync_service_sid) \
                        .documents \
                        .list(**kwargs)
        return api_response
    
    def create_sync_document(self, sync_service_sid, kwargs):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .documents \
            .create(**kwargs)
        return api_response
    
    def update_sync_document(self, sync_service_sid, sync_document_sid_or_unique_name, kwargs):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .documents(sync_document_sid_or_unique_name) \
            .update(**kwargs)
        return api_response
    
    def fetch_sync_document(self, sync_service_sid, sync_document_sid_or_unique_name):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .documents(sync_document_sid_or_unique_name) \
            .fetch()
        return api_response

    def delete_sync_document(self, sync_service_sid, sync_document_sid_or_unique_name):
        api_response = self.twilio_client.sync \
            .v1 \
            .services(sync_service_sid) \
            .documents(sync_document_sid_or_unique_name) \
            .delete()
        return api_response
    
    def create_flow(self, kwargs):
        api_response = self.twilio_client.studio.v2.flows.create(**kwargs)
        return api_response

    def fetch_flow(self, flow_sid):
        api_response = self.twilio_client.studio.v2.flows(flow_sid).fetch()
        return api_response

class CustomTwilioHttpClient(TwilioHttpClient):
    def __init__(self):
        self.response = None

    def request(self, method, url, params=None, data=None, headers=None, auth=None, timeout=None,
                allow_redirects=False):
        headers = {
            'X-Twilio-Webhook-Enabled': 'true'
        }
        # Here you can change the URL, headers and other request parameters
        kwargs = {
            'method': method.upper(),
            'url': url,
            'params': params,
            'data': data,
            'headers': headers,
            'auth': auth,
        }

        session = Session()
        request = Request(**kwargs)

        prepped_request = session.prepare_request(request)
        session.proxies.update({
            'http': os.getenv('HTTP_PROXY'),
            'https': os.getenv('HTTPS_PROXY')
        })
        response = session.send(
            prepped_request,
            allow_redirects=allow_redirects,
            timeout=timeout,
        )

        return Response(int(response.status_code), response.text)
