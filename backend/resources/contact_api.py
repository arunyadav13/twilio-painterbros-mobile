from flask_restful import Resource, request
from helpers.db_helper import DBHelper

class ContactSearchApi(Resource):
    def post(self):
        input = request.get_json()
        tenant_id = input.get('tenant_id', None)
        subtenant_id = input.get('subtenant_id', None)
        user_identity = input.get('user_identity', None)
        search_query = input.get('search_query', None)

        if not tenant_id or not subtenant_id or not user_identity:
            return {'message': 'Missing required parameters'}, 400

        search_contact_response = DBHelper().search_contact(tenant_id, search_query,
            {
                'subtenant_id': subtenant_id,
                'user_identity': user_identity
            })

        return search_contact_response