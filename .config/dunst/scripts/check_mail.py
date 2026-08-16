#!/usr/bin/env python3
import imaplib
import time
import subprocess
import email
import os
from email.header import decode_header

# --- Configuration ---
GMAIL_EMAIL = "aditya.akkannavar@gmail.com" 
GMAIL_APP_PASSWORD = "bnke bkkd rejs isje"
# Use the icon we just downloaded
ICON_PATH = os.path.expanduser("~/.config/dunst/gmail.svg")

# Runtime memory only. Clears when the PC shuts down.
seen_uids = set()
is_first_run = True

def decode_mime_words(s):
    """Properly decodes =?utf-8?Q? headers into clean text."""
    if not s:
        return "Unknown"
    decoded_words = decode_header(s)
    result = []
    for word, encoding in decoded_words:
        if isinstance(word, bytes):
            try:
                result.append(word.decode(encoding or 'utf-8', errors='ignore'))
            except LookupError:
                result.append(word.decode('utf-8', errors='ignore'))
        else:
            result.append(word)
    return "".join(result)

def check_gmail():
    global is_first_run
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        mail.select("INBOX", readonly=True)
        
        # Search for unread emails
        status, response = mail.uid("search", None, "UNSEEN")
        if status != "OK" or not response[0]:
            is_first_run = False
            mail.logout()
            return

        current_unseen_uids = response[0].split()
        
        for msg_uid in current_unseen_uids:
            uid_str = msg_uid.decode('utf-8')
            
            # 1. On startup, just memorize the old unread mail silently
            if is_first_run:
                seen_uids.add(uid_str)
                continue
                
            # 2. If it is genuinely a new email that arrived during this session
            if uid_str not in seen_uids:
                # Fetch ONLY headers to save bandwidth
                status, data = mail.uid("fetch", msg_uid, "(BODY[HEADER.FIELDS (FROM SUBJECT)])")
                if status == "OK" and data[0]:
                    raw_headers = data[0][1]
                    msg = email.message_from_bytes(raw_headers)
                    
                    # Decode the ugly UTF-8 strings into normal text
                    subject = decode_mime_words(msg.get("Subject", "No Subject"))
                    sender = decode_mime_words(msg.get("From", "Unknown Sender"))
                    
                    sender = sender.replace("<", "(").replace(">", ")")
                    
                    # Fire Dunst notification with the custom Gmail icon
                    subprocess.run([
                        "dunstify", 
                        "-a", "Gmail",
                        "-u", "normal",
                        "-i", ICON_PATH,
                        "New Email", 
                        f"<b>From:</b> {sender}\n<b>Subject:</b> {subject}"
                    ])
                    
                seen_uids.add(uid_str)
                time.sleep(0.5)
                
        is_first_run = False
        mail.logout()
    except Exception:
        pass

def main():
    while True:
        check_gmail()
        time.sleep(60)

if __name__ == "__main__":
    main()
