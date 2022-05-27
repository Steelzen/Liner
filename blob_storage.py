import local_constants
from google.cloud import storage

def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    
    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)

def addFile(file):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME) 
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(file.filename) 
    blob.upload_from_file(file)

def delete_blob(blob_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME) 
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.blob(blob_name)
    blob.delete()  