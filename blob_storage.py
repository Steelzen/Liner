import local_constants
from typing import List
from google.cloud import storage

def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    
    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)


def set_bucket_public_iam(
    bucket_name: str = local_constants.PROJECT_STORAGE_BUCKET,
    members: List[str] = ["allUsers"],
):
    """Set a public IAM Policy to bucket"""

    storage_client = storage.Client()
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    policy = bucket.get_iam_policy(requested_policy_version=3)
    policy.bindings.append(
        {"role": "roles/storage.objectViewer", "members": members}
    )

    bucket.set_iam_policy(policy)


def upload_blob(file, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_file(file) 

def delete_blob(blob_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME) 
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.blob(blob_name)
    blob.delete()  
