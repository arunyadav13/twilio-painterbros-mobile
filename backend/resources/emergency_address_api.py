from flask import request
from flask_restful import Resource
from helpers.twilio_helper import TwilioHelper
from twilio.base.exceptions import TwilioException

class EmergencyAddressApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        kwargs = input.get('kwargs', None)
                        
        if not tenant_id or not subtenant_id or not kwargs or not kwargs.get('customer_name', None) or not kwargs.get('street', None) or not kwargs.get('city', None) or not kwargs.get('region', None) or not kwargs.get('postal_code', None) or not kwargs.get('iso_country', None):
            return {'message': 'Kindly fill out the mandatory fields'}, 400
        try:
            if kwargs.get('iso_country', '').lower().strip() in ['usa', 'united states', 'united states of america', 'us']:
                kwargs['iso_country'] = 'US'
            
            kwargs['emergency_enabled'] = True
            twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
            api_response = twilio_helper.create_emergency_address(kwargs)
            return {'data': {
                    'sid': api_response.sid,
                    'date_created': str(api_response.date_created),
                    'emergency_enabled': api_response.emergency_enabled,
                    'customer_name': api_response.customer_name,
                    'street': api_response.street,
                    'city': api_response.city,
                    'region': api_response.region,
                    'postal_code': api_response.postal_code,
                    'iso_country': api_response.iso_country,
                    'validated': api_response.validated,
                    'verified': api_response.verified,
                }
            }
        
        except TwilioException as e:
            return {'message': e.msg.replace('Unable to create record: ', '')}, 206 if e.code == 21629 else 417
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500
        
    def put(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        emergency_address_sid = input.get('emergency_address_sid', None)
        kwargs = input.get('kwargs', None)
                        
        if not tenant_id or not subtenant_id or not emergency_address_sid or not kwargs or not kwargs.get('customer_name', None) or not kwargs.get('street', None) or not kwargs.get('city', None) or not kwargs.get('region', None) or not kwargs.get('postal_code', None):
            return {'message': 'Kindly fill out the mandatory fields'}, 400
        
        if kwargs.get('iso_country', '').lower().strip() in ['usa', 'united states', 'united states of america', 'us']:
            kwargs['iso_country'] = 'US' 
        
        try:
            twilio_helper = TwilioHelper({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
            api_response = twilio_helper.create_emergency_address(kwargs)
            # api_response = twilio_helper.update_emergency_address(emergency_address_sid, kwargs)
            return {'data': {
                    'sid': api_response.sid,
                    'date_created': str(api_response.date_created),
                    'emergency_enabled': api_response.emergency_enabled,
                    'customer_name': api_response.customer_name,
                    'street': api_response.street,
                    'city': api_response.city,
                    'region': api_response.region,
                    'postal_code': api_response.postal_code,
                    'iso_country': api_response.iso_country,
                    'validated': api_response.validated,
                    'verified': api_response.verified,
                }
            }
        
        except TwilioException as e:
            return {'message': e.msg.replace('Unable to update record: ', '')}, 417
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500