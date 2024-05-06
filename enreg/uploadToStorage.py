import logging
import os

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.views import generic
from dotenv import load_dotenv

#Env File loading here
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def upload_to_space(file_content, directory_name, file_name):
    try:
        access_key = os.environ["SPACE_ACCESS_KEY"]
        secret_key = os.environ["SPACE_SECRET"]
        region_name = os.environ["SPACE_REGION"]
        endpoint = os.environ["SPACE_ENDPOINT"]
        service_name = os.environ["SERVICE_NAME"]
        space_name = os.environ["SPACE_NAME"]
    except KeyError as e:
        logging.error("Missing environment variable: %s", e)
        return None

    session = boto3.session.Session()

    try:
        s3 = session.client(
            service_name,
            region_name=region_name,
            endpoint_url=f"https://{space_name}.{region_name}.{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
    except Exception as e:
        logging.error("Error creating S3 client: %s", e)
        return None

    # Check if the directory exists, if not, create it
    try:
        s3.head_object(Bucket=space_name, Key=directory_name)
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            try:
                s3.put_object(Bucket=space_name, Key=directory_name)
            except ClientError as e:
                logging.error("Error creating directory: %s", e)
                return None
        else:
            logging.error("Error checking directory existence: %s", e)
            return None

    # Upload the file to the specified directory
    try:
        response = s3.put_object(
            Bucket=space_name,
            Key=f"{directory_name}/{file_name}",
            Body=file_content
        )
        logging.info("File uploaded successfully.")
        return f"{directory_name}/{file_name}"  # Return the path to the uploaded file in the bucket
    except ClientError as e:
        logging.error("Error uploading file: %s", e)
        return None


def download_file_from_space(file_path):
    print('File Path')
    file_path = f"{file_path}"
    print(file_path)
    try:
        access_key = os.environ["SPACE_ACCESS_KEY"]
        secret_key = os.environ["SPACE_SECRET"]
        region_name = os.environ["SPACE_REGION"]
        endpoint = os.environ["SPACE_ENDPOINT"]
        service_name = os.environ["SERVICE_NAME"]
        space_name = os.environ["SPACE_NAME"]
    except KeyError as e:
        logging.error("Missing environment variable: %s", e)
        return None

    session = boto3.session.Session()

    try:
        s3 = session.client(
            service_name,
            region_name=region_name,
            endpoint_url=f"https://{space_name}.{region_name}.{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        # Check if the file exists
        try:
            response = s3.head_object(Bucket=space_name, Key=file_path)
            print('File Found')

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logging.error("File not found.")
                print('File not found')
                print(e)
                return None
            else:
                print(e)
                logging.error("Error checking file existence: %s", e)
                return None

        # If the file exists, download it
        if response:
            # Download file from Space
            response = s3.get_object(Bucket=space_name, Key=file_path)
            file_content = response['Body'].read()

            if file_content:
                print('File received')
                return file_content
            else:
                logging.error("Empty file content.")
                return None
        else:
            logging.error("File not found.")
            return None

    except NoCredentialsError:
        logging.error("Credentials not available.")
        return None
    except Exception as e:
        print(e)
        logging.error("Error downloading file: %s", e)
        return None




