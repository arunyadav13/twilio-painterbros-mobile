import os, requests

from datetime import timedelta, datetime
from flask_restful import Resource
from flask import Response, request
from twilio.twiml.voice_response import VoiceResponse
from helpers.db_helper import DBHelper
from helpers.app_helper import AppHelper
from helpers.azure_helper import AzureHelper
from requests.auth import HTTPBasicAuth

class VoicemailRecordingCompleteApi(Resource):
    def post(self):
        response = VoiceResponse()
        response.say('You message has been sent. Thank you for calling.')
        return Response(str(response), mimetype='text/xml')

class VoicemailRecordingStatusCallbackApi(Resource):
    def post(self):
        phone_number = request.args.get('phone_number')
        tenant_id = request.args.get('tenant_id')
        subtenant_id = request.args.get('subtenant_id')
        call_sid = request.form.get('CallSid')
        recording_url = request.form.get('RecordingUrl')
        recording_sid = request.form.get('RecordingSid')
        
        subaccount = DBHelper().get_subaccount({'tenant_id': tenant_id, 'subtenant_id': subtenant_id})
        r = requests.get(recording_url, stream=True, auth = HTTPBasicAuth(subaccount['account_sid'], subaccount['auth_token']))
        voicemail_path = os.path.dirname(os.path.realpath(__file__)) + '/../temp/voicemail/'
        if not os.path.exists(voicemail_path):
            os.makedirs(voicemail_path)
        voicemail_filename = recording_sid + '.mp3'
        file = open(voicemail_path + voicemail_filename, 'wb')
        file.write(r.raw.read())
        file.close()

        azure_helper = AzureHelper()
        container_name = 'voicemail'
        container_client = azure_helper.get_container_client({'container_name': container_name})
        if not container_client.exists():
            azure_helper.create_container(container_name)
        azure_helper.upload_blob(voicemail_path + '/' + voicemail_filename, {'container': container_name, 'blob': voicemail_filename})
        os.remove(voicemail_path + '/' + voicemail_filename)
        temp_files = os.listdir(voicemail_path + '/')
        for temp_file in temp_files:
            if os.path.getmtime(voicemail_path + '/' + temp_file) < (datetime.utcnow() - timedelta(days=1)).timestamp():
                os.remove(voicemail_path + '/' + temp_file)
       
        DBHelper().save_voicemail(request.form, phone_number, container_name + '/' + voicemail_filename)
        AppHelper().push_voicemail_to_sync_list(call_sid)
        return 'success'

class VoicemailTranscriptionCompleteApi(Resource):
    def post(self):
        recording_sid = request.form.get('RecordingSid')
        transcription_text = request.form.get('TranscriptionText')
        DBHelper().save_voicemail({'RecordingSid': recording_sid, 'TranscriptionText': transcription_text})
        return 'success'