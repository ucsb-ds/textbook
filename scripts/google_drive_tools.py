#!/usr/bin/env python3

import os
import requests
from pprint import pprint

import os
import csv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pprint import pprint
import time
import sys
import re

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


import re
from googleapiclient.errors import HttpError
import google.oauth2.credentials



SLEEP=1.1

# Define the required scopes
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.activity.readonly",
    "https://www.googleapis.com/auth/contacts.readonly",
    'https://www.googleapis.com/auth/chat.spaces',
    "https://www.googleapis.com/auth/chat.memberships",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/chat.messages",
]


# Authenticate and build the Drive API service
def authenticate():
    """
    Authenticate the user and return a Google Drive API service object.
    Credentials (google client id and client secret) are expected to be in 'credentials.json'.
    The file 
    This function checks for existing credentials in 'token.json'.
    If not found or invalid, it prompts the user to log in and saves the new credentials.
    """
    creds = None
    CREDENTIALS_FILE = "credentials.json"
    GOOGLE_DRIVE_TOKEN_FILE = "google_drive_token.json"

    if os.environ.get("GOOGLE_DRIVE_TOKEN"):
        print("Using GOOGLE_DRIVE_TOKEN environment variable for credentials.")
        # write contents of GOOGLE_DRIVE_TOKEN to a file
        if not os.path.exists(GOOGLE_DRIVE_TOKEN_FILE):
            with open(GOOGLE_DRIVE_TOKEN_FILE, "w") as f:
                f.write(os.environ["GOOGLE_DRIVE_TOKEN"])
        creds = Credentials.from_authorized_user_file("google_drive_token.json", SCOPES)
        if not creds or not creds.valid:
            print("Credentials are invalid or expired. Please re-authenticate.")
            sys.exit(1)
        else:
            print("Credentials loaded from environment variable.")
            return build("drive", "v3", credentials=creds)
    # Check if the credentials file exists

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Credentials file '{CREDENTIALS_FILE}' not found. Please ensure it exists.")
        sys.exit(1)
    if os.path.exists(GOOGLE_DRIVE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_DRIVE_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_DRIVE_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)




def get_drive_file_from_url(service, url, message=""):
    """
    Extracts the file or folder ID from a Google Drive URL and returns the file metadata.
    
    Parameters:
        service: Authenticated Google Drive API service instance.
        url (str): Google Drive file or folder URL.

    Returns:
        dict: File metadata (e.g., {'id': '...', 'name': '...'}), or None if not found or invalid.
    """
    # Common patterns to extract file or folder ID
    patterns = [
        r'colab\.research\.google\.com\/drive\/([a-zA-Z0-9_-]+)', # colab.research.google.com/drive/FOLDER_ID
        r'drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)',     # /file/d/FILE_ID
        r'drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)',     # open?id=FILE_ID
        r'drive\.google\.com\/uc\?id=([a-zA-Z0-9_-]+)',       # uc?id=FILE_ID
        r'drive\.google\.com\/drive\/folders\/([a-zA-Z0-9_-]+)', # /folders/FOLDER_ID
        r'drive\.google\.com\/drive\/u\/\d\/folders\/([a-zA-Z0-9_-]+)', # /u/2/folders/FOLDER_ID
    ]
    
    file_id = None
    for pattern in patterns:
        # Use re.search to find the first match in the URL
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            break
    
    if not file_id:
        print(f"Unable to extract file ID from URL {url} {message}")
        return None
    
    try:
        file = service.files().get(fileId=file_id, fields="id, name, mimeType, webViewLink").execute()
        return file
    except HttpError as error:
        print(f"An error occurred in get_drive_file_from_url: {error} {message}")
        return None



# Get a folder (optionally creating it)
def get_folder(service, name, parent_id=None, create_if_not_exists=False, DEBUG=False):
    if DEBUG:
        print(f"Getting folder: {name} under parent ID: {parent_id}")
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name, webViewLink)")
        .execute()
    )
    folders = results.get("files", [])
    num_results = len(folders)
    if num_results>1:
        print(f"Warning: get_folder for name={name} returned {num_results} results");
    # If the folder already exists, return its ID
    if folders:
        return folders[0]

    if not create_if_not_exists:
        print(
            f"Folder '{name}' not found; returning none"
        )
        return None

    print(f"Creating folder {name}")
    # Otherwise, create a new folder and return it's ID
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id] if parent_id else [],
    }
    folder = service.files().create(body=metadata, fields="id, name, webViewLink").execute()
    return folder


# Get files by name (optionally under a parent folder)
def get_files(service, name, parent_id=None):
    print(f"Getting file: {name} under parent ID: {parent_id}")
    query = f"name='{name}'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name, webViewLink)")
        .execute()
    )
    files = results.get("files", [])
    num_results = len(files)
    if num_results>1:
        print(f"Warning: get_file for name={name} returned {num_results} results");
    # If the folder already exists, return its ID
    return files

def get_all_files_in_folder(service, folder_id):
    """
    Get all files in a specific Google Drive folder.
    """
    query = f"'{folder_id}' in parents"
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name, webViewLink)")
        .execute()
    )
    return results.get("files", [])

# Get a file or folder by its ID
def get_by_id(service, id):
    try:
        result = service.files().get(fileId=id, fields="id, name, mimeType, webViewLink, parents").execute()
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def get_folders(service, parent_id):
    print(f"Getting all folders under parent ID: {parent_id}")
    query = f"mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents"
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name, webViewLink)")
        .execute()
    )
    results['files'].sort(key=lambda x: x['name'])
    return results


def get_set_of_emails_with_write_access(service, folder_id):
    """
    Get a list of people with write access to a specific folder.
    """
    try:
        permissions = service.permissions().list(
            fileId=folder_id,
            fields='permissions(id,emailAddress,role,type)'
        ).execute()
        people_with_write_access = []
        for permission in permissions.get('permissions', []):
            if (
                permission.get('role') == 'writer'
                and permission.get('type') == 'user'
                and 'emailAddress' in permission
            ):
                people_with_write_access.append(permission['emailAddress'])
        return set(people_with_write_access)
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def read_staff_emails(file_path):
    """
    Read staff emails from a CSV file.
    The file should have a column named 'email'.
    """
    staff_emails = set()
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                email = row.get('email')
                if email:
                    staff_emails.add(email.strip())
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
    return staff_emails


def read_staff_emails_with_sections(file_path, sections=["10am","11am","noon","1pm"]):
    """
    Read staff emails and their sections from a CSV file.
    The file should have columns named 'email' and 'section'.
    Returns a dictionary mapping email to section.
    """
    
    convert_string_to_bool = lambda s: str(s).strip().lower() in ['1','true','yes','y','x']
    
    section_to_staff_emails = {}
    for section in sections:
        section_to_staff_emails[section] = set()
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                email = row.get('email')
                for section in sections:
                    add_to_this_section = convert_string_to_bool(row.get(section, False))
                    if add_to_this_section and email:
                        section_to_staff_emails[section].add(email.strip())
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
    return section_to_staff_emails

def get_students_with_write_access(service, folder_id, staff_email_set):
    """
    Get a set of students with write access to a specific folder,
    excluding staff members.
    """
    people_with_write_access = get_set_of_emails_with_write_access(service, folder_id)
    students_with_write_access = people_with_write_access - staff_email_set
    return students_with_write_access


def get_folder_creator_email(service, folder_id):
    """
    Get the email address of the user who created a specific folder.
    Uses the 'owners' field from the Drive API file metadata.
    """
    try:
        folder = service.files().get(fileId=folder_id, fields="owners").execute()
        owners = folder.get("owners", [])
        if owners:
            return owners[0].get("emailAddress")
        else:
            print(f"No owner found for folder ID: {folder_id}")
            return None
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

# Share folder with email
def give_write_access_to_folder(service, folder, email):
    # Give the user with the email address `email` write access to the folder
    # file_id is the ID of the folder
    # email is the email address of the user to share with

    # Create a permission object
    permission = {"type": "user", "role": "writer", "emailAddress": email}
    # Create the permission using the Drive API
    service.permissions().create(
        fileId=folder['id'], body=permission, fields="id", sendNotificationEmail=False
    ).execute()
    print(f"Granted write access to {email} on folder {folder['name']} (ID: {folder['id']}).")

def revoke_write_access_to_folder(service, folder, email):
    """
    Revoke write access to a folder for a specific email address.
    """
    file_id = folder['id']
    try:
        # Get the permissions for the file, including email addresses
        permissions = service.permissions().list(
            fileId=file_id,
            fields='permissions(id,emailAddress,role,type)'
        ).execute()
        for permission in permissions.get('permissions', []):
            if permission.get('emailAddress') == email and permission.get('role') == 'writer':
                # Revoke the permission
                service.permissions().delete(fileId=file_id, permissionId=permission['id']).execute()
                print(f"Revoked write access for {email} on folder {folder}.")
                return
        print(f"No write access found for {email} on folder {folder}.")
    except HttpError as error:
        print(f"An error occurred: {error}")

def adjust_folder_permissions(service, folder_id, student_email_set, staff_email_set):
    """
    Adjust permissions for a folder to ensure the correct set of students and staff have write access.
    This function will remove write access for any email not in the student or staff sets,
    and will ensure that all emails in the student and staff sets have write access.
    """
    # Get current permissions
    
    folder = get_by_id(service, folder_id)
    current_writers = get_set_of_emails_with_write_access(service, folder_id)
    creator_email = get_folder_creator_email(service, folder_id)
    
    correct_writers = student_email_set.union(staff_email_set) - {creator_email}
    # Remove write access for emails not in the correct set
    for email in current_writers - correct_writers:
        revoke_write_access_to_folder(service, folder, email)
    # Add write access for emails in the correct set that don't have it
    for email in correct_writers - current_writers:
        give_write_access_to_folder(service, folder, email)
   
def authenticate_spaces():
    creds = None
    OAUTH_CLIENT_FILE = "credentials.json"
    TOKEN_FILE = "spaces_token.json"
    if os.path.exists(TOKEN_FILE):
        print(f"Token file {TOKEN_FILE} exists. Loading...")
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
            TOKEN_FILE, SCOPES
        )
        if not set(SCOPES).issubset(set(creds.scopes)):
            print("⚠️ Token does not have the required scopes. Re-authenticating...")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
            print(f"Token saved to {TOKEN_FILE}")

    return creds
   
def get_session():
    authenticated_creds = authenticate_spaces()
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {authenticated_creds.token}"})
    return session
  
  
def list_all_spaces_with_display_names(session: requests.Session):
    list_url = "https://chat.googleapis.com/v1/spaces"
    params = {"pageSize": 250}

    all_spaces = []

    while True:
        response = session.get(list_url, params=params)
        if response.status_code != 200:
            print(f"⚠️ Failed to list spaces: {response.status_code} {response.text}")
            break

        data = response.json()
        all_spaces.extend(data.get("spaces", []))

        if "nextPageToken" in data:
            params["pageToken"] = data["nextPageToken"]
        else:
            break

    return all_spaces
  
def get_matching_spaces(session, display_name_pattern):
    existing_spaces = get_existing_spaces(session)
    result = []
    for space in existing_spaces:
        if re.match(display_name_pattern, space.get("displayName", "")):
            result.append(space)
    return result
  
def get_existing_spaces(session):
    """Fetch and cache all existing spaces."""
    if not hasattr(get_existing_spaces, "_cache"):
        get_existing_spaces._cache = None

    if get_existing_spaces._cache is not None:
        return get_existing_spaces._cache

    all_spaces = list_all_spaces_with_display_names(session)

    get_existing_spaces._cache = all_spaces
    return all_spaces
  
def get_existing_members_emails(session, space):
    members_url = f"https://chat.googleapis.com/v1/{space['name']}/members"
    members_resp = session.get(members_url)
    if members_resp.status_code != 200:
        print(
            f"⚠️ Failed to get members for {space['displayName']}: {members_resp.text}"
        )
        return None
    existing_members = members_resp.json().get("memberships", [])

    # Extract user IDs from the member data
    user_ids = []
    for member in existing_members:
        member_info = member.get("member", {})
        user_id = member_info.get("name", "").split("/")[-1]
        if user_id:
            user_ids.append(user_id)

    # Use People API to fetch emails for the user IDs
    emails = []
    for user_id in user_ids:
        email_entry = person_id_to_ucsb_email(session, user_id)
        if email_entry:
            emails.append(email_entry)

    return emails

def get_person(session, user_id):
    # print(f"{function_name()}, called by {called_by()} Getting person {user_id}")
    people_url = f"https://people.googleapis.com/v1/people/{user_id}?personFields=emailAddresses,names"
    resp = session.get(people_url)
    time.sleep(SLEEP)  # Respect rate limits
    if resp.status_code != 200:
        print(f"⚠️ Failed to get person {user_id}: {resp.text}")
        sys.exit(1)
        return None
    person = resp.json()
    return person


def person_to_ucsb_email(person):
    if not person:
        return None
    email_addresses = person.get("emailAddresses", [])
    for email_entry in email_addresses:
        email_entry = email_entry.get("value")
        if email_entry and email_entry.endswith("@ucsb.edu"):
            return email_entry
    return None


def person_id_to_ucsb_email(session, person_id):
    person = get_person(session, person_id)
    if not person:
        return None
    return person_to_ucsb_email(person)

  
def adjust_space_permissions(
    session, space, group_member_emails, staff_email_set, DEBUG=False
):
    """
    Adjust permissions for a Google Chat space.
    Ensures that all group members and staff have write access.
    """
    print(f"Adjusting permissions for space: {space['displayName']} (ID: {space['name']})")
    
    # Get existing members' emails
    current_emails = set(get_existing_members_emails(session, space))
      
    correct_emails = group_member_emails.union(staff_email_set) 
    # Remove write access for emails not in the correct set
    for email in current_emails - correct_emails:
        if DEBUG:
            print(f"Should remove access for {email} to space {space['displayName']} (ID: {space['name']})") 
        remove_member_from_space(session, space, email)
    # Add write access for emails in the correct set that don't have it
    for email in correct_emails - current_emails:
        if DEBUG:
            print(f"Should add access for {email} to space {space['displayName']} (ID: {space['name']})")
        add_member_to_space(session, space, email)


def get_recent_messages(session, space):
    messages_url = f"https://chat.googleapis.com/v1/{space['name']}/messages"
    params = {"pageSize": 50, "orderBy": "createTime asc"}
    resp = session.get(messages_url, params=params)
    if resp.status_code != 200:
        print(
            f"⚠️ Failed to get recent messages for {space['displayName']}: {resp.text}"
        )
        return None
    messages = resp.json().get("messages", [])

    # Add the URL of each message to the message data
    for message in messages:
        message_id = message.get("name", "").split("/")[-1]
        if message_id:
            message["url"] = (
                f"https://chat.google.com/room/{space['name'].split('/')[1]}/{message_id}"
            )

    return messages

def rename_space(session, space, new_display_name):
    space_name = space.get("name")
    url = f"https://chat.googleapis.com/v1/{space_name}?updateMask=displayName"
    payload = {
        "displayName": new_display_name
    }
    response = session.patch(url, json=payload)

    if response.status_code == 200:
        print("Space renamed successfully.")
        return response.json()
    else:
        print(f"Failed to rename space: {response.status_code}")
        print(response.text)
        return None
    
def get_space_manager_email(session, space):
    """
    Get the owner of a Google Chat space.
    This function assumes that the first member with 'owner' role is the space owner.
    """
    members_url = f"https://chat.googleapis.com/v1/{space['name']}/members"
    response = session.get(members_url)
    
    if response.status_code != 200:
        print(f"⚠️ Failed to get members for {space['displayName']}: {response.text}")
        return None
    
    members = response.json().get("memberships", [])
    
    owner = None
    for member in members:
        if member.get("role") == "ROLE_MANAGER":
            owner = member
            break
    if owner:
        owner_info = owner.get("member", {})
        owner_id = owner_info.get("name", "").split("/")[-1]
        if owner_id:
            owner_email = person_id_to_ucsb_email(session, owner_id)
            if owner_email:
                return owner_email                    
    return None

def add_member_to_space(session, space, email, DEBUG=False):
    """
    Add a member to a Google Chat space by their email address.
    """
    if DEBUG:
        print(f"Adding {email} to space {space['displayName']} (ID: {space['name']})")
    time.sleep(SLEEP)  # Respect rate limits
    
    invite_url = f"https://chat.googleapis.com/v1/{space['name']}/members"
    member_payload = {"member": {"name": f"users/{email}", "type": "HUMAN"}}
    response = session.post(invite_url, json=member_payload)
    
    if response.status_code == 200:
        if DEBUG:
            print(f"Successfully added {email} to space {space['displayName']}.")
    else:
        print(f"⚠️ Failed to add {email} to space {space['displayName']}: {response.status_code}")
        print(response.text)

def remove_member_from_space(session, space, email, DEBUG=False):
    """
    Remove a member from a Google Chat space by their email address.
    """
    if DEBUG:
        print(f"Removing {email} from space {space['displayName']} (ID: {space['name']})")
    time.sleep(SLEEP)  # Respect rate limits
    remove_url = f"https://chat.googleapis.com/v1/{space['name']}/members/{email}"
    response = session.delete(remove_url)
    if response.status_code == 200 or response.status_code == 204:
        if DEBUG:
            print(f"Successfully removed {email} from space {space['displayName']}.")
    else:
        print(f"⚠️ Failed to remove {email} from space {space['displayName']}: {response.status_code}")
        print(response.text)
        

def mark_space_unused(session, space):
    """
    Mark a space as unused by deleting it.
    """
    print(f"Marking space {space['displayName']} (ID: {space['name']}) as unused.")
    
    rename_space(session, space, "unused")
    
    space_manager_email  = get_space_manager_email(session, space)
    
    # Remove all members from the space
    emails = set(get_existing_members_emails(session, space)) - {space_manager_email}

    for email in emails:
        remove_member_from_space(session, space, email)
    remove_member_from_space(session, space, space_manager_email)  

    print(f"Space {space['displayName']} (ID: {space['name']}) marked as unused.")
  
  
def create_new_space(session, space_display_name):
    time.sleep(SLEEP)  # Respect rate limits
    create_space_payload = {"spaceType": "SPACE", "displayName": space_display_name}
    resp = session.post(
        "https://chat.googleapis.com/v1/spaces", json=create_space_payload
    )
    if resp.status_code != 200:
        print(f"❌ Failed to create space {space_display_name}: {resp.text}")
        return None

    space = resp.json()
    space_name = space["name"]
    print(f"🚀 Created space {space_display_name}: {space_name}")
    return space
  
def create_folders_for_groups_set_with_members(service, parent_folder_id, group_set_with_members, staff_email_set=set()):
    """
    Create folders for each group in the group set under the specified parent folder.
    Each folder is named "{group_name}".
    """
    group_name_to_url = {}
    for group in group_set_with_members:
        group_name = group['name']
        folder_name = f"{group_name}"
        folder = get_folder(service, folder_name, parent_id=parent_folder_id, create_if_not_exists=True)
        group_name_to_url[group_name] = folder['webViewLink']
        if folder:
            print(f"Folder for group '{group_name}': {folder['name']} (ID: {folder['id']})")
        else:
            print(f"Failed to create or retrieve folder for group '{group_name}'.")
        members_spreadsheet_tools.create_sheet_for_group(service, group, folder, staff_email_set)
    return group_name_to_url
  
  
def send_message_if_not_sent_recently(session, space, message_text):
    """
    Send a message to a Google Chat space if the same message hasn't been sent recently.
    """
    time_window_seconds = 3600 * 24 * 30  # 30 days
    recent_messages = get_recent_messages(session, space)

    current_time = time.time()
    for message in recent_messages:
        if message.get("text") == message_text:
            message_time_str = message.get("createTime")
            if message_time_str:
                message_time = time.mktime(time.strptime(message_time_str, "%Y-%m-%dT%H:%M:%S.%fZ"))
                if (current_time - message_time) < time_window_seconds:
                    print(f"Message already sent recently to space {space['displayName']}. Skipping.")
                    return

    # Send the message
    messages_url = f"https://chat.googleapis.com/v1/{space['name']}/messages"
    payload = {"text": message_text}
    response = session.post(messages_url, json=payload)
    if response.status_code == 200:
        print(f"Message sent to space {space['displayName']}.")
    else:
        print(f"Failed to send message to space {space['displayName']}: {response.status_code}")
        print(response.text)

def get_data_file_name_to_id_mapping(folder_name="inferential_thinking_notebooks"):
    """
    Get a mapping of data file names to their IDs.
    """
    try:
        service = authenticate()
        print("Google Drive API service authenticated successfully.")
    except Exception as e:
        print(f"An error occurred during authentication: {e}")
        sys.exit(1)
    
    print("Getting folder set from Google Drive...")
    inferential_thinking_notebook_folder = get_folder(service,
                                      folder_name,
                                      create_if_not_exists=False)
    if inferential_thinking_notebook_folder is None:
        print("Inferential Thinking Notebook folder not found.")
        sys.exit(1)

    data_folder = get_folder(service,
                                "data",
                                parent_id=inferential_thinking_notebook_folder['id'],
                                create_if_not_exists=False)
    if data_folder is None:
        print("Data folder not found.")
        sys.exit(1)

    all_data_files = get_all_files_in_folder(service, data_folder['id'])

    data_file_dict = {file['name']: file for file in all_data_files}

    return data_file_dict

if __name__ == "__main__":
    data_file_dict = get_data_file_name_to_id_mapping()
    pprint(data_file_dict)
   