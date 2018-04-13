import os
import sys
import json

from Tkinter import *
from tkCommonDialog import Dialog
from tkMessageBox import showerror

from multiprocessing import Pipe
from multiprocessing import Process
from multiprocessing import freeze_support

from pop import ProcessWrapper

class Chooser(Dialog):
    command = "tk_chooseDirectory"
    def _fixresult(self, widget, result):
        if result:
            # keep directory until next time
            self.options["initialdir"] = result
        self.directory = result # compatibility
        return result

class MailDownloader(Frame):

    def __init__(self, client, parent=None):
        Frame.__init__(self, parent)
        self.master.protocol("WM_DELETE_WINDOW", self.cleanup)

        self.client = client
        self.process = None

        self.grid()
        self.layout_form()
        self.remember_config()

        self.after(100, self.check_status)

    def save_config(self):
        config = {
            "host": self.host.get(),
            "user": self.user.get(),
            "password": self.password.get(),
            "selected_dir": self.selected_dir.get(),
            "port": self.port.get(),
        }

        home_dir = os.path.expanduser('~')
        with open(os.path.join(home_dir, "mail_dl.config"), 'w') as f:
            f.write(json.dumps(config))

    def config_location(self):
        home_dir = os.path.expanduser('~')
        return os.path.join(home_dir, "mail_dl.config")

    def remember_config(self):
        config = {}
        try:
            with open(self.config_location(), 'r') as f:
                config.update(json.loads(f.read()))
        except:
            pass
        self.host.set(config.get('host', ''))
        self.port.set(config.get('port', 110))
        self.user.set(config.get('user', ''))
        self.password.set(config.get('password', ''))
        self.selected_dir.set(config.get('selected_dir', ''))

    def layout_form(self):
        self.create_text_row("host", label="Host:", row=0, default="")
        self.create_text_row("port", label="Port:", row=1, default=110)
        self.create_text_row("user", label="User:", row=2, default="")
        self.create_text_row("password", label="Password:", row=3, default="")
        self.create_directory_dialog()
        self.create_process_control()

    def create_text_row(self, varname, label="", row=0, default=None):
        Label(self, text=label).grid(row=row, sticky=W, padx=10, pady=2)
        setattr(self, varname, StringVar())
        entry = Entry(self, textvariable=getattr(self, varname))
        getattr(self, varname).set(default)
        field_name = "%s_field" % varname
        setattr(self, field_name, entry)
        getattr(self, field_name).grid(row=row, column=1, sticky=W, padx=10, pady=2)

    def create_directory_dialog(self):
        self.chooser = Chooser()
        self.selected_dir = StringVar()
        self.selected_dir.set("None Selected")
        self.selected_dir_label = Label(self, textvariable=self.selected_dir)
        self.selected_dir_label.grid(sticky=W, row=4, column=1, padx=5, pady=2)
        self.select_btn = Button(self, text='Choose Folder', command=self.set_dir)
        self.select_btn.grid(row=4, sticky=W, padx=5, pady=2)

    def create_process_control(self):
        self.start_stop = Button(self, text='Start Downloading',
                                 command=self.toggle_process)
        self.start_stop.grid(row=5, sticky=E, padx=5, pady=2)
        self.process_status = StringVar()
        self.process_status_label = Label(self, textvariable=self.process_status)
        self.process_status_label.grid(row=5, column=1, sticky=W, padx=5, pady=2)

    def toggle_process(self):
        if self.process:
            self.terminate_process()
        else:
            self.save_config()
            self.start_process()

    def set_dir(self):
        directory = self.chooser.show()
        self.selected_dir.set(directory)

    def terminate_process(self):
        try:
            self.process.terminate()
        except:
            pass

        self.start_stop.config(text="Start Downloader")
        self.process_status.set("Downloader Stopped")
        self.process = None

    def cleanup(self):
        sys.exit()

    def get_form_data(self):
        self.host.get(),
        self.user.get(),
        self.password.get(),
        self.selected_dir.get(),
        self.port.get(),

    def start_process(self):
        "If not a valid directory, alert the user and abort"
        if not self.check_directory(self.selected_dir.get()):
            showerror("Directory doesn't exist",
                "Please choose a valid directory")
        else:

            self.pipe, child_pipe = Pipe()
            self.process = Process(target=self.client, 
                args=(
                    self.host.get(),
                    self.user.get(),
                    self.password.get(),
                    self.selected_dir.get(),
                    self.port.get(),
                ),
                kwargs={
                    'pipe': child_pipe,
                    'debuglevel': 0,
                }
            )
            self.process.name = "Email Downloader"
            self.process.start()
            self.process_status.set("Downloader Started")
            self.start_stop.config(text="Stop Uploading")

    def check_directory(self, path):
        path = str(path)
        return os.path.exists(path)

    def check_status(self):
        if self.process and self.pipe:
            if self.pipe.poll():
                self.process_msg(self.pipe.recv())
        self.after(100, self.check_status)

    def process_msg(self, msg):
        if msg['type'] == "FATAL":
            self.terminate_process()

freeze_support()
app = MailDownloader(ProcessWrapper)
app.master.title("Mail Downloader")
app.mainloop()
