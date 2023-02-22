from azure.storage.blob import BlobServiceClient, ContainerClient, generate_blob_sas, BlobSasPermissions
from config.constant import AZURE_STORAGE_CONNECTION_STRING
from datetime import datetime, timedelta

class AzureHelper:
    
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        
    def create_container(self, container_name):
        return self.blob_service_client.create_container(container_name)
    
    def get_container_client(self, kwargs):
        kwargs['conn_str'] = AZURE_STORAGE_CONNECTION_STRING
        result = ContainerClient.from_connection_string(**kwargs)
        return result
    
    def upload_blob(self, upload_file_path, kwargs):
        blob_client = self.blob_service_client.get_blob_client(**kwargs)
        with open(file=upload_file_path, mode="rb") as data:
            blob_client.upload_blob(data)
        return 'success'
        
    def generate_blob_sas(self, kwargs):
        kwargs['account_name'] = self.blob_service_client.credential.account_name
        kwargs['account_key'] = self.blob_service_client.credential.account_key
        if 'permission' not in kwargs:
            kwargs['permission'] = BlobSasPermissions(read=True, write=False, create=False)
        if 'expiry' not in kwargs:
            kwargs['expiry'] = datetime.utcnow() + timedelta(days=1)
        sas_blob = generate_blob_sas(**kwargs)
        return 'https://'+self.blob_service_client.credential.account_name+'.blob.core.windows.net/'+ kwargs['container_name'] +'/'+ kwargs['blob_name'] +'?'+ sas_blob
    