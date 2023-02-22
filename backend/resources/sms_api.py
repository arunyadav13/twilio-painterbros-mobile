from flask import request
from flask_restful import Resource
from helpers.twilio_helper import TwilioHelper
from config.constant import TWILIO_MESSAGING_SERVICE_ACCOUNT_SID, TWILIO_MESSAGING_SERVICE_AUTH_TOKEN, TWILIO_MESSAGING_SERVICE_FROM_PHONE_NUMBER

class SendSMSApi(Resource):
    def post(self):
        try:
            input = request.get_json()
            body = input.get('body', None)
            to = input.get('to', None)
            from_ = input.get('from_', TWILIO_MESSAGING_SERVICE_FROM_PHONE_NUMBER)
            
            if not body or not to or not from_:
                return {'message': 'Kindly fill out the mandatory fields'}, 400
            
            twilio_helper = TwilioHelper({'account_sid': TWILIO_MESSAGING_SERVICE_ACCOUNT_SID, 'auth_token': TWILIO_MESSAGING_SERVICE_AUTH_TOKEN})
            api_response = twilio_helper.send_message({'from_': from_, 'body': body, 'to': to})
            return {
                'sid': api_response.sid,
                'body': api_response.body,
                'direction': api_response.direction,
                'error_code': api_response.error_code,
                'error_message': api_response.error_message,
                'from': api_response.from_,
                'to': api_response.to,
                'date_created': str(api_response.date_created),
                'date_sent': str(api_response.date_sent) if api_response.date_sent else api_response.date_sent,
                'date_updated': str(api_response.date_updated),
                'status': api_response.status,
            }
        
        except Exception as e:
            return {'message': 'An application error occurred, please contact administrator', 'details': str(e)}, 500