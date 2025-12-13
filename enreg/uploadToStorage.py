import logging
import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from django.views import generic
from dotenv import load_dotenv

#Env File loading here
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def _get_spaces_client():
    """Create and return a boto3 client configured for DigitalOcean Spaces."""
    try:
        access_key = os.environ["SPACE_ACCESS_KEY"]
        secret_key = os.environ["SPACE_SECRET"]
        region_name = os.environ["SPACE_REGION"]
        endpoint = os.environ["SPACE_ENDPOINT"]  # e.g. digitaloceanspaces.com
        service_name = os.environ.get("SERVICE_NAME", "s3")
    except KeyError as e:
        logging.error("Missing environment variable: %s", e)
        return None

    session = boto3.session.Session()
    try:
        # IMPORTANT: endpoint_url should NOT include the bucket name
        endpoint_url = f"https://{region_name}.{endpoint}"
        return session.client(
            service_name,
            region_name=region_name,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )
    except Exception as e:
        logging.error("Error creating S3 client: %s", e)
        return None


def _normalize_key(key: str) -> str:
    """Ensure object Key has no leading slash and no duplicate separators."""
    if not key:
        return ""
    # Strip leading slashes
    key = key.lstrip('/')
    # Avoid accidental double slashes
    while '//' in key:
        key = key.replace('//', '/')
    return key


def upload_to_space(file_content, directory_name, file_name):
    try:
        space_name = os.environ["SPACE_NAME"]
    except KeyError as e:
        logging.error("Missing environment variable: %s", e)
        return None

    s3 = _get_spaces_client()
    if s3 is None:
        return None

    # Check if the directory exists, if not, create it
    # Normalize directory prefix and create a zero-byte marker if missing.
    dir_key = _normalize_key(directory_name)
    # Use trailing slash for folder-like prefix marker
    if dir_key and not dir_key.endswith('/'):
        dir_key_marker = dir_key + '/'
    else:
        dir_key_marker = dir_key

    try:
        if dir_key_marker:
            s3.head_object(Bucket=space_name, Key=dir_key_marker)
    except ClientError as e:
        if e.response.get('Error', {}).get('Code') in ('404', 'NoSuchKey', 'NotFound'):
            try:
                if dir_key_marker:
                    s3.put_object(Bucket=space_name, Key=dir_key_marker)
            except ClientError as e2:
                logging.error("Error creating directory marker '%s': %s", dir_key_marker, e2)
                return None
        else:
            logging.error("Error checking directory existence: %s", e)
            return None

    # Upload the file to the specified directory
    try:
        file_key = _normalize_key(f"{dir_key}/{file_name}" if dir_key else file_name)
        response = s3.put_object(
            Bucket=space_name,
            Key=file_key,
            Body=file_content
        )
        logging.info("File uploaded successfully.")
        return file_key  # Return the path to the uploaded file in the bucket
    except ClientError as e:
        logging.error("Error uploading file: %s", e)
        return None


def download_file_from_space(file_path):
    print('File Path')
    file_path = f"{file_path}"
    print(file_path)
    try:
        space_name = os.environ["SPACE_NAME"]
    except KeyError as e:
        logging.error("Missing environment variable: %s", e)
        return None

    s3 = _get_spaces_client()
    if s3 is None:
        return None

    key = _normalize_key(file_path)
    try:
        # Check if the file exists
        response = s3.head_object(Bucket=space_name, Key=key)
        print('File Found')

        # If the file exists, download it
        if response:
            obj = s3.get_object(Bucket=space_name, Key=key)
            file_content = obj['Body'].read()

            if file_content:
                print('File received')
                return file_content
            else:
                logging.error("Empty file content.")
                return None
        else:
            logging.error("File not found.")
            return None

    except ClientError as e:
        code = e.response.get('Error', {}).get('Code')
        if code in ('404', 'NoSuchKey', 'NotFound'):
            logging.error("File not found for bucket='%s' key='%s'", space_name, key)
            print('File not found')
            print(e)
            return None
        else:
            print(e)
            logging.error("Error accessing object (head/get): %s", e)
            return None
    except NoCredentialsError:
        logging.error("Credentials not available.")
        return None
    except Exception as e:
        print(e)
        logging.error("Error downloading file: %s", e)
        return None




