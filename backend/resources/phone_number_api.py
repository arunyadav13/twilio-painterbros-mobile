import urllib.parse
from flask import request
from flask_restful import Resource
from helpers.twilio_helper import TwilioHelper
from helpers.db_helper import DBHelper
from models.subaccount import SubAccount
from twilio.base.exceptions import TwilioException
from models.subaccount import SubAccount
from config.constant import SERVER_APP_BASE_URL

class PhoneNumberApi(Resource):
    def get(self):
        tenant_id = request.args.get('tenant_id', None)
        subtenant_id = request.args.get('subtenant_id', None)
        phone_number = request.args.get('number', None)
        phone_number = urllib.parse.quote_plus(phone_number)

        if not tenant_id or not subtenant_id or not phone_number:
            return {'message': 'Kindly fill out the mandatory fields'}, 400
        
        # TODO: use "tenant_id" and "subtenant_id" filter (as kwargs) while getting the phone number.
        phone_number = DBHelper().get_phone_number(phone_number)

        phone_number = phone_number if phone_number and phone_number['subaccount']['tenant_id'] == tenant_id and phone_number['subaccount']['subtenant_id'] == subtenant_id else dict()
        if phone_number and phone_number['subaccount']:
            phone_number.pop('subaccount')
        return phone_number
    
    def put(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        phone_number_sid = input.get('phone_number_sid', None)
        emergency_address_sid = input.get('emergency_address_sid', None)
        
        if not tenant_id or not subtenant_id or not phone_number_sid:
            return {'message': 'Kindly fill out the mandatory fields'}, 400
        try:
            twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
            api_response = twilio_helper.update_phone_number(phone_number_sid, {'emergency_address_sid': emergency_address_sid})
            return {'data': {
                        'sid': api_response.sid,
                        'date_created': str(api_response.date_created),
                        'friendly_name': api_response.friendly_name,
                        'emergency_status': api_response.emergency_status,
                        'emergency_address_sid': api_response.emergency_address_sid,
                        'emergency_address_status': api_response.emergency_address_status,
                        'capabilities': api_response.capabilities,
                        'phone_number': api_response.phone_number
                    }}
        
        except TwilioException as e:
            return {'message': e.msg.replace('Unable to update record: ', '')}, 417
            
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500

class SearchPhoneNumberApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        kwargs = input.get('kwargs', None)
        
        if not tenant_id or not subtenant_id or not kwargs:
            return {'message': 'Kindly fill out the mandatory fields'}, 400
        try:
            twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
            kwargs['voice_enabled'] = True
            data = []
            phone_numbers = twilio_helper.search_available_local_phone_numbers(kwargs)
            for record in phone_numbers:
                structure = dict()
                structure['friendly_name'] = record.friendly_name
                structure['phone_number'] = record.phone_number
                structure['locality'] = record.locality
                structure['region'] = record.region
                data.append(structure)
            return data
        
        except TwilioException as e:
            return {'message': e.msg}, 417
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500

class BuyPhoneNumberApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        emergency_address_sid = input.get('emergency_address_sid', None)
        kwargs = input.get('kwargs', None)
        
        if not tenant_id or not subtenant_id or not kwargs or not kwargs.get('phone_number'):
            return {'message': 'Kindly fill out the mandatory fields'}, 400
        try:
            db_helper = DBHelper()
            subaccount = SubAccount.query.filter_by(status = True, tenant_id = tenant_id, subtenant_id=subtenant_id).first()
            if not (subaccount and subaccount.messaging_service_sid) :
                return {'message': 'Subaccount is not configured properly, please contact administrator'}, 400
            phone_number = db_helper.get_phone_number(kwargs.get('phone_number'))
            if phone_number:
                return {'message': 'You have already purchased this phone number'}, 409
            twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
            kwargs['voice_method'] = 'POST'
            kwargs['voice_url'] = request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/call/inbound'
            kwargs['sms_method'] = 'POST'
            kwargs['sms_url'] = request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/message/inbound'
            kwargs['status_callback_method'] = 'POST'
            kwargs['status_callback'] = request.host_url.rstrip('/').replace('http:', 'https:') + SERVER_APP_BASE_URL + '/api/call/inbound/status-callback'
            api_response = twilio_helper.buy_phone_number(kwargs)
            twilio_helper.add_phone_number_to_messaging_service(subaccount.messaging_service_sid, {'phone_number_sid': api_response.sid})
            db_helper.add_phone_number(subaccount.id, api_response)
            # TODO: Commented temporarily untill handling release phone number
            # if emergency_address_sid:
            #     twilio_helper.update_phone_number(api_response.sid, {'emergency_address_sid': emergency_address_sid})
            #     api_response = twilio_helper.fetch_phone_number(api_response.sid)
            return { 'data': {
                        'sid': api_response.sid,
                        'date_created': str(api_response.date_created),
                        'friendly_name': api_response.friendly_name,
                        'capabilities': api_response.capabilities,
                        'phone_number': api_response.phone_number,
                        'account_sid': api_response.account_sid
                    } }
        
        except TwilioException as e:
            return {'message': e.msg}, 417
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500

class ReleasePhoneNumberApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        phone_number_sid = input.get('phone_number_sid', None)
        
        if not tenant_id or not subtenant_id or not phone_number_sid:
            return {'message': 'Kindly fill out the mandatory fields'}, 400
        try:
            db_helper = DBHelper()
            # TODO: Handle release phone number if it is already mapped with emergency address
            twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
            twilio_helper.delete_phone_number(phone_number_sid)
            db_helper.delete_phone_number(phone_number_sid)
            return {'message':'Released successfully'}
        
        except TwilioException as e:
            return {'message': e.msg.replace('Unable to delete record: ', '')}, 417
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500