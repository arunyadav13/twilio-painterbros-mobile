from flask import request
from flask_restful import Resource
from helpers.db_helper import DBHelper
from config.constant import TEMP_IVR_ZIPCODES, TEMP_IVR_PRELEAD_CREATION_SKIP_LIST

class CheckZipcodeApi(Resource):
    def post(self):
        input = request.get_json()
        zipcode = input.get('zipcode', '')
        from_ = input.get('from_', '')
        zipcode = zipcode.replace('*', '')
        no_input_retry_count = input.get('no_input_retry_count', 0)
        no_input_retry_count = int(no_input_retry_count.strip()) if no_input_retry_count else 0
        invalid_zipcode_retry_count = input.get('invalid_zipcode_retry_count', 0)
        invalid_zipcode_retry_count = int(invalid_zipcode_retry_count.strip()) if invalid_zipcode_retry_count else 0
        results = {'is_valid_zipcode': False, 'franchise': None}
        validation_status = False
        db_helper = DBHelper()
        if zipcode:
            us_city = db_helper.get_us_city_by_zipcode(zipcode)    
            if us_city:
                validation_status = True
        if validation_status or no_input_retry_count >= 3 or invalid_zipcode_retry_count >= 2:
            subtenant = db_helper.get_subtenant_by_zipcode(zipcode)
            if from_ not in TEMP_IVR_PRELEAD_CREATION_SKIP_LIST:
                db_helper.create_prelead(from_, zipcode if zipcode else '00000')
            # TODO Make this section dynamic before moving to production
            # if subtenant:
                # db_helper.create_prelead(from_, zipcode)
                # results['is_valid_zipcode'] = True
                # results['franchise']['number'] = subtenant['Mobile']
            available_zipcodes = TEMP_IVR_ZIPCODES
            if no_input_retry_count >= 3 or invalid_zipcode_retry_count >= 2:
                results['is_valid_zipcode'] = True
                results['franchise'] = dict()
                results['franchise']['number'] = available_zipcodes[list(available_zipcodes.keys())[0]]
            else:
                if zipcode in available_zipcodes.keys():
                    results['is_valid_zipcode'] = True
                    results['franchise'] = dict()
                    results['franchise']['number'] = available_zipcodes[zipcode]
        return results