import os
import sys
import time
import email
import random
import base64
import poplib

class PopClient(object):

    def __init__(self, hostname, port=110, debuglevel=0):
        self.hostname = hostname
        self.port = port
        self.debuglevel = debuglevel

    def connect(self):
        self.connection = poplib.POP3(self.hostname, self.port)
        self.connection.set_debuglevel(self.debuglevel)

    def login(self, username, password):
        self.connection.user(username)
        self.connection.pass_(password)

    def get_messages(self, delete=False):
        msg_ids = self.connection.list()
        for i in range(1, len(msg_ids[1]) + 1):
            msg_str = "\n".join(self.connection.retr(i)[1])
            msg = email.message_from_string(msg_str)
            if delete:
                self.connection.dele(i)
            yield msg

    def download_image_from_msg(self, msg, path):
        for part in msg.walk():
            if part.get_content_type() in ('image/jpeg', 'image/jpg', 'image/png', 'image/gif'):
                filename = part.get_filename('unknown-%d.jpg' % random.randint(0, sys.maxint))
                image_data = part.get_payload()
                base, ext = os.path.splitext(filename)
                filename = "%s-%s%s" % (base, random.randint(0,9999), ext) 
                with open(os.path.join(path, filename), 'wb') as f: f.write(base64.b64decode(image_data))

    def download_new_images(self, path, delete=False):
        downloaded = 0
        for msg in self.get_messages(delete=delete):
            downloaded += 1
            self.download_image_from_msg(msg, path)
        return downloaded

    def logout(self):
        try:
            self.connection.quit()
        except:
            pass

class ProcessWrapper():

    def __init__(self, hostname, username, password, path, port, pipe=None, debuglevel=0):
        self.path = path
        self.pipe = pipe
        self.client = PopClient(hostname, port=port, debuglevel=debuglevel)
        self.poll_for_images(username, password)

    def poll_for_images(self, username, password):
        last = time.time()

        while True:
            now = time.time()
            if now - last > 3:

                "We have to connect on every try because POP only deletes on quit"

                try:
                    self.client.connect()
                    self.client.login(username, password)
                except Exception as e:
                    self.send_msg("Could not login. Try Again: %s" % e)

                strtime =  time.strftime("%H:%M:%S")
                self.send_msg("Checking for new images: %s" % strtime)

                try:
                    downloaded = self.client.download_new_images(self.path, delete=True)
                    if downloaded:
                        self.send_msg("Downloaded %s" % downloaded)
                except Exception as e:
                    self.send_msg("Could not download messages. Try Again: %s" % e)

                self.client.logout()
                last = now

            time.sleep(2)

    def send_msg(self, msg, type='message'):
        print msg
        if self.pipe:
            self.pipe.send({'type': type, 'msg': msg})
        else:
            print("%s: %s" % (type, msg))

if __name__ == '__main__':
    hostname = ''
    username = ''
    password = ''

    client = PopClient(hostname, port=110) 
    client.connect()
    client.login(username, password)
    client.download_new_images('.')

    client.logout()
