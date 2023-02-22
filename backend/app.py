from flask import Flask
from flask_cors import CORS
from config.constant import SERVER_APP_BASE_URL, SQLALCHEMY_DATABASE_URI, SECRET_KEY, CORS_ALLOWED_ORIGINS
from config.db import db
from flask_restful import Api
from flask_migrate import Migrate

from resources.subaccount_api import SubAccountApi
from resources.access_token import AccessTokenApi
from resources.call_api import AbortWarmTrandferApi, StartWarmTransferApi, CompleteWarmTransferApi, ResumeCallApi, HoldCallApi, EndConferenceApi, OutboundCallApi, OutboundCallConferenceStatusCallbackApi, ConferenceCreateParticipantApi, ConferenceCreateParticipantStatusCallbackApi, ConferenceRemoveParticipantApi, InboundCallApi, InboundCallConferenceStatusCallbackApi, InboundCallConferenceCreateParticipantStatusCallbackApi, InboundCallStatusCallbackApi
from resources.sync_api import SyncServiceWebhookApi
from resources.contact_api import ContactSearchApi
from resources.phone_number_api import PhoneNumberApi, SearchPhoneNumberApi, BuyPhoneNumberApi, ReleasePhoneNumberApi
from resources.emergency_address_api import EmergencyAddressApi
from resources.message_api import InboundMessageApi
from resources.conversation_api import ConversationWebhookApi, SMSConversationApi, SMSApi, ConversationsByParticipantNumbersApi
from resources.sms_api import SendSMSApi
from resources.ivr_api import CheckZipcodeApi
from resources.voicemail_api import VoicemailRecordingCompleteApi, VoicemailRecordingStatusCallbackApi, VoicemailTranscriptionCompleteApi
from resources.temp_api import ResetApi, GetSyncListData
from resources.azure_api import AzureBlobLinkApi
from resources.preferences_api import PreferencesApi

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


CORS(app, origins=CORS_ALLOWED_ORIGINS)
db.init_app(app)
migrate = Migrate(app, db)

api = Api(app, prefix = SERVER_APP_BASE_URL + "/api")
api.add_resource(InboundCallApi, '/call/inbound', methods = ["POST"])
api.add_resource(InboundCallStatusCallbackApi, '/call/inbound/status-callback', methods = ["POST"])
api.add_resource(InboundCallConferenceStatusCallbackApi, '/call/inbound/conference/status-callback', methods = ["POST"])
api.add_resource(InboundCallConferenceCreateParticipantStatusCallbackApi, '/call/inbound/conference/create-participant/status-callback', methods = ["POST"])
api.add_resource(OutboundCallApi, '/call/outbound', methods = ["POST"])
api.add_resource(OutboundCallConferenceStatusCallbackApi, '/call/outbound/conference/status-callback', methods = ["POST"])
api.add_resource(ConferenceCreateParticipantApi, '/call/conference/create-participant', methods = ["POST"])
api.add_resource(ConferenceRemoveParticipantApi, '/call/conference/participant/remove', methods = ["POST"])
api.add_resource(ConferenceCreateParticipantStatusCallbackApi, '/call/conference/create-participant/status-callback', methods = ["POST"])
api.add_resource(EndConferenceApi, '/conference/end', methods = ["POST"])
api.add_resource(AccessTokenApi, '/access-token', methods = ["POST"])
api.add_resource(SyncServiceWebhookApi, '/sync/webhook', methods = ["POST"])
api.add_resource(ContactSearchApi, '/search/contact', methods = ["POST"])
api.add_resource(HoldCallApi, '/call/hold', methods = ["POST"])
api.add_resource(ResumeCallApi, '/call/resume', methods = ["POST"])
api.add_resource(VoicemailRecordingCompleteApi, '/call/voicemail/recording/complete', methods = ["POST"])
api.add_resource(VoicemailRecordingStatusCallbackApi, '/call/voicemail/recording/status-callback', methods = ["POST"])
api.add_resource(VoicemailTranscriptionCompleteApi, '/call/voicemail/transcription/complete', methods = ["POST"])
api.add_resource(StartWarmTransferApi, '/call/warm-transfer', methods = ["POST"])
api.add_resource(CompleteWarmTransferApi, '/call/warm-transfer/complete', methods = ["POST"])
api.add_resource(AbortWarmTrandferApi, '/call/warm-transfer/abort', methods = ["POST"])

api.add_resource(SubAccountApi, '/sub-account', methods = ["POST", "PUT"])
api.add_resource(PhoneNumberApi, '/phone-number', methods = ["GET", "PUT"])
api.add_resource(SearchPhoneNumberApi, '/phone-number/search', methods = ["POST"])
api.add_resource(BuyPhoneNumberApi, '/phone-number/purchase', methods = ["POST"])
api.add_resource(ReleasePhoneNumberApi, '/phone-number/release', methods = ["POST"])
api.add_resource(EmergencyAddressApi, '/emergency-address', methods = ["POST", "PUT"])
api.add_resource(InboundMessageApi, '/message/inbound', methods = ["POST"])
api.add_resource(SendSMSApi, '/sms/send', methods = ["POST"])
api.add_resource(SMSConversationApi, '/conversation', methods = ["POST"])
api.add_resource(ConversationsByParticipantNumbersApi, '/conversation/by-participant-numbers', methods = ["POST"])
api.add_resource(SMSApi, '/conversation/sms', methods = ["GET"])
api.add_resource(ConversationWebhookApi, '/conversation/webhook', methods = ["POST"])
api.add_resource(CheckZipcodeApi, '/ivr/check-zipcode', methods = ["POST"])
api.add_resource(AzureBlobLinkApi, '/azure/blob/link', methods = ["GET"])
api.add_resource(PreferencesApi, '/preferences', methods = ["POST", "PUT"])

api.add_resource(ResetApi, '/temp/reset', methods = ["POST"])
api.add_resource(GetSyncListData, '/temp/get-synclist-data', methods = ["POST"])

@app.route(SERVER_APP_BASE_URL + "/", methods = ["GET"])
def home():
   return 'Hello from PainterBros!'

if __name__ == '__main__':
   app.run(debug=True, host="0.0.0.0")