from flask_restful import Resource
from flask import request, redirect
from helpers.azure_helper import AzureHelper

class AzureBlobLinkApi(Resource):
    def get(self):
        path = request.args.get('path', '').strip()
        if not path:
            return {'message': 'Kindly fill out the mandatory fields'}, 400
        voicemail_path = path.split('/')
        vm_url =  AzureHelper().generate_blob_sas({'container_name': voicemail_path[0], 'blob_name': voicemail_path[1]})
        return redirect(vm_url)