import urllib.parse
from flask import request
from flask_restful import Resource
from helpers.db_helper import DBHelper
from helpers.constants import Constants


class PreferencesApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        number = input.get('number', None)

        if not tenant_id or not subtenant_id or not number:
            return {'message': 'Kindly fill out the mandatory fields'}, 400

        db_helper = DBHelper()
        phone_number = db_helper.get_phone_number(number)

        call_forwarding_rules = db_helper.get_call_forwarding_rules({'phone_number_id': phone_number['id']})
        for cfr in call_forwarding_rules:
            cfr.pop('id')
            cfr.pop('number_type')
            cfr.pop('status')

            contact = db_helper.get_contact(tenant_id, {'number': cfr['number']})
            cfr['name'] = contact['name'] if contact else ''
            
        response = dict()
        response['call_forwarding_rules'] = call_forwarding_rules
        return response

    def put(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        number = input.get('number', None)
        kwargs = input.get('kwargs', None)

        if not tenant_id or not subtenant_id or not number or not kwargs:
            return {'message': 'Kindly fill out the mandatory fields'}, 400

        db_helper = DBHelper()
        phone_number = db_helper.get_phone_number(number)

        """
        it is required to check "if kwargs.get('call_forwarding_rules') != None".
        when all forwarding rules are deleted from frontend, "call_forwarding_rules" will become an empty list.
        standard "if call_forwarding_rules" check will give False as output and existing rules will not be deleted from DB.
        """
        if kwargs.get('call_forwarding_rules') != None:
            existing_cfrs = db_helper.get_call_forwarding_rules({'phone_number_id': phone_number['id']})
            for existing_cfr in existing_cfrs:
                db_helper.delete_call_forwarding_rule(existing_cfr['id'])

            for i, new_cfr in enumerate(kwargs.get('call_forwarding_rules')):
                if i < len(existing_cfrs) and new_cfr['number'] == existing_cfrs[i]['number'] and new_cfr['duration'] == existing_cfrs[i]['duration']:
                    db_helper.restore_call_forwarding_rule(existing_cfrs[i]['id'])
                else:
                    number_type = Constants.PhoneNumberTypes.EXTERNAL.name
                    if new_cfr['number'] == phone_number['number']:
                        number_type = Constants.PhoneNumberTypes.SELF.name
                    else:
                        pn = db_helper.get_phone_number(new_cfr['number'])
                        if pn and pn['subaccount']['tenant_id'] == tenant_id:
                            number_type = Constants.PhoneNumberTypes.INTERNAL.name

                    cfr = db_helper.add_call_forwarding_rule(
                        {
                            'phone_number_id':  phone_number['id'],
                            'number':  new_cfr['number'],
                            'number_type':  number_type,
                            'duration':  new_cfr['duration'],
                        }
                    )

        return 'success'