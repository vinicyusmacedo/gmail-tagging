from create_labels import get_creds
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError


def search_messages(service, query, pageToken=None):
    print(f"Querying pageToken {pageToken}")
    message_list = []
    messages = {}
    try:
        if pageToken:
            messages = service.users().messages().list(
                userId='me',
                includeSpamTrash=True,
                q=query,
                pageToken=pageToken
            ).execute()
        else:
            messages = service.users().messages().list(
                userId='me',
                includeSpamTrash=True,
                q=query
            ).execute()
    except HttpError as e:
        if '409' not in str(e):
            print(f"Unexpected error occurred {e}") 
    
    if messages.get('resultSizeEstimate') > 0:
        message_ids = [message.get('id') for message in messages.get('messages')]
        message_list.extend(message_ids)
        nextPageToken = messages.get('nextPageToken')
        if nextPageToken:
            message_list.extend(search_messages(service, query, nextPageToken))
    return message_list



def main():
    service = build('gmail', 'v1', credentials=get_creds())
    try:
        print("Getting current filters")
        filters = service.users().settings().filters().list(userId='me').execute()
        print(f"{len(filters.get('filter'))} filters found")
        for mail_filter in filters.get('filter'):
            from_mail = mail_filter.get('criteria').get('from')
            print(f"Filter {from_mail}")
            labels = mail_filter.get('action').get('addLabelIds')
            messages_to_filter = search_messages(service, f"from:{from_mail} has:nouserlabels")
            if messages_to_filter:
                req = {
                    'ids': messages_to_filter,
                    'addLabelIds': labels
                }
                print(f"Applying filter for {from_mail} to labels {labels} to {len(messages_to_filter)} messages")
                service.users().messages().batchModify(userId='me', body=req).execute()
            else:
                print(f"Filter for {from_mail} has no untagged messages")
    except HttpError as e:
        if '409' not in str(e):
            print(f"Unexpected error occurred {e}") 


if __name__ == '__main__':
    main()
