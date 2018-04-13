import os
import sys
import time
import email
import random
import base64
import imaplib

class ImapClient(object):

    def __init__(self, hostname, port=993):
        self.connection = imaplib.IMAP4_SSL(hostname, port)

    def select_mailbox(self, mailbox):
        self.connection.select(mailbox)

    def login(self, username, password):
        self.connection.login(username, password)

    def logout(self):
        self.connection.logout()

    def get_message_ids(self, key):
        ids = []
        typ, msg_ids = self.connection.search(None, key)

        if typ == 'OK' and len(msg_ids):
            ids = msg_ids[0].split(' ')

        return ids

    def get_messages(self, ids):
        msgs = []

        id_str = ",".join(ids)
        typ, msg_data = self.connection.fetch(id_str, '(RFC822)')
        if typ == 'OK':
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msgs.append(email.message_from_string(response_part[1]))
        return msgs

    def flag_messages(self, ids, flags):
        id_str = ",".join(ids)
        typ, response = self.connection.store(id_str, '+FLAGS', flags)

    def download_new_images(self, path):
        ids = self.get_message_ids('(NEW)')
        msgs = self.get_messages(ids)
        for msg in msgs:
            for part in msg.walk():
                if part.get_content_type() == 'image/jpeg':
                    filename = part.get_filename('unknown-%d.jpg' % random.randint(0, sys.maxint))
                    image_data = part.get_payload()
                    with open(os.path.join(path, filename), 'wb') as f:
                        f.write(base64.b64decode(image_data))

        self.flag_messages(ids, r'\Seen')

class ProcessWrapper():

    def __init__(self, hostname, username, password, path, pipe=None):
        self.path = path
        self.pipe = pipe

        self.client = ImapClient(hostname)

        try:
            self.client.login(username, password)
        except:
            send_msg("Could not login. Try Again")

        self.client.select_mailbox('INBOX')
        self.poll_for_images()

    def poll_for_images(self):
        last = time.time()

        while True:
            now = time.time()
            if now - last > 3:
                strtime =  time.strftime("%H:%M:%S")
                self.send_msg("Checking for new images: %s" % strtime)
                try:
                    self.client.download_new_images(self.path)
                except:
                    self.send_msg("Could not download messages. Try Again")
                last = now
                time.sleep(2)

    def send_msg(self, msg, type='message'):
        if self.pipe:
            self.pipe.send({'type': type, 'msg': msg})
        else:
            print("%s: %s" % (type, msg))

if __name__ == '__main__':

    if len(sys.argv) == 1:
        print "usage: imap.py hostname username password"
        exit()

    hostname = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    client = ImapClient(hostname) 
    client.login(username, password)
    client.select_mailbox('INBOX')
    ids = client.get_message_ids('(NEW)')

    client.logout()
