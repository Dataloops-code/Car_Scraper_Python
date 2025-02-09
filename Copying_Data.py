from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json

def get_yesterday_date():
    """Get yesterday's date in the required format."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def authenticate_google_drive():
    """Authenticate with Google Drive API using service account."""
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    try:
        # Get credentials from environment variables
        credentials_json = os.environ.get('ANALYSIS_COPY')
        refresh_token = os.environ.get('GOOGLE_REFRESH_TOKEN')
        
        if not credentials_json:
            raise ValueError("ANALYSIS_COPY environment variable not found")
        if not refresh_token:
            raise ValueError("GOOGLE_REFRESH_TOKEN environment variable not found")
            
        credentials_info = json.loads(credentials_json)
        
        # Create credentials object with all required fields
        creds = Credentials(
            token=None,  # Token will be obtained through refresh
            refresh_token=refresh_token,
            token_uri=credentials_info['installed']['token_uri'],
            client_id=credentials_info['installed']['client_id'],
            client_secret=credentials_info['installed']['client_secret'],
            scopes=SCOPES
        )
        
        # Force a refresh to get a valid token
        request = Request()
        creds.refresh(request)
        
        return build('drive', 'v3', credentials=creds)
    
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise

def copy_folder(service, source_folder_id, dest_folder_id, folder_name):
    """Copy a folder from source to destination."""
    try:
        # Check if folder already exists in destination
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{dest_folder_id}' in parents"
        results = service.files().list(q=query).execute()
        existing_folders = results.get('files', [])
        
        if existing_folders:
            print(f"Folder {folder_name} already exists in destination. Skipping copy.")
            return
            
        # Create new folder in destination
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [dest_folder_id]
        }
        new_folder = service.files().create(body=folder_metadata).execute()
        
        # List all files in source folder
        query = f"'{source_folder_id}' in parents"
        results = service.files().list(q=query).execute()
        files = results.get('files', [])
        
        # Copy each file to new folder
        for file in files:
            copied_file = {
                'name': file['name'],
                'parents': [new_folder['id']]
            }
            service.files().copy(
                fileId=file['id'],
                body=copied_file
            ).execute()
            print(f"Copied file: {file['name']}")
            
    except Exception as e:
        print(f"Error copying folder: {str(e)}")
        raise

def main():
    """Main function to copy yesterday's folder."""
    source_folder_id = "11pG4Jwy1gJUbz7cILT6sfzmLD5f75nqU"
    dest_folder_id = "1vqooBw99wWVr2SdaQeyRBtIdgpeZMlRo"
    
    try:
        yesterday = get_yesterday_date()
        service = authenticate_google_drive()
        
        # Search for folder with yesterday's date in source
        query = f"name='{yesterday}' and mimeType='application/vnd.google-apps.folder' and '{source_folder_id}' in parents"
        results = service.files().list(q=query).execute()
        folders = results.get('files', [])
        
        if not folders:
            print(f"No folder found with name {yesterday}")
            return
        
        # Copy the folder
        source_date_folder = folders[0]
        copy_folder(service, source_date_folder['id'], dest_folder_id, yesterday)
        print(f"Successfully copied folder {yesterday}")
        
    except Exception as e:
        print(f"An error occurred in main: {str(e)}")
        raise

if __name__ == '__main__':
    main()
