from tkinter import *
from domain.user import User
from threading import Thread

import json

from apiconsumer.apiconsumer import APIConsumer
from domain.commandinterpreter import CommandInterpreter

class Chat(Frame):

  def __init__(self, user, master=None):
    Frame.__init__(self, master)
    self.root = master
    self.user = user
    self.grid()
    self.window = master
    self.window.protocol('WM_DELETE_WINDOW', self.quit)
    self.running = True
    self.changed_screen = False
    self.next_screen = None
    # Init components
    self.init_components()
    self.tcp = None
    self.connect()
    self.receive_thread = Thread(target=self.receive)
    self.receive_thread.daemon = True
    self.receive_thread.start()

  def init_components(self):
    self.root.bind('<Return>', self.send)
    # Title
    self.window.title("Near - Chat")
    self.window.resizable(width=False, height=False)
    self.configure(background="white")
    # Public chat
    label_t = Label(self, text="Public chat", width=10, background="white")
    label_t.grid(row=0, column=0, padx=(5, 5), pady=(7, 7), sticky=W)
    # Logoff
    label_l = Button(self, text="Logoff", width=10, command=self.logoff)
    label_l.grid(row=0, column=9, padx=(5, 5), pady=(7, 7), sticky=E)
    # Messages
    self.messages = Text(self, width=62, height=24, background="white")
    self.messages.grid(row=1, column=0, columnspan=10, sticky=W+E)
    self.messages.config(state=DISABLED)
    # Message
    self.message = Entry(self, width=20, background="white")
    self.message.grid(row=2, column=0, columnspan=8, padx=(5, 0), pady=(7, 7), sticky=W+E)
    # Send
    send = Button(self, text="Send", width=10, command=self.send)
    send.grid(row=2, column=9, padx=(5, 5), pady=(7, 7), sticky=E)

  def receive(self):
    """Handles receiving of messages."""
    while self.running:
      try:
        msg = self.tcp.recv(1024).decode("utf8")

        mymsg = json.loads(msg)
        messagetodisplay = mymsg['message']
        shalltranslate = mymsg['translate']

        if msg != "":
          self.messages.config(state=NORMAL)
          if shalltranslate == True:
              if mymsg['language'] == self.user.language:
                  self.messages.insert(END, mymsg['username'] + ': ' + mymsg['message'] + '\n')
              else:
                  apiConsumer = APIConsumer()
                  parameters = { 'message' : mymsg['message'], 'dstLanguage' : self.user.language, 'srcLanguage' : mymsg['language'] }
                  self.messages.insert(END, mymsg['username'] + ': ' + str(apiConsumer.callPost('/translate', parameters, 'translatedTo')) + '\n')
          else:
              self.messages.insert(END, mymsg['username'] + ': ' + mymsg['message'] + '\n')
          self.messages.config(state=DISABLED)
          self.messages.see(END)
          self.message.delete(0, END)
      except OSError: # Possibly client has left the chat.
        break

  def connect(self):
    import socket
    HOST = '127.0.0.1' # Server IP Address
    PORT = 33000 # Server port
    self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest = (HOST, PORT)
    self.tcp.connect(dest)

  def send(self, event=NONE):
    message_content = self.message.get()

    self.messages.config(state=NORMAL)
    #self.messages.insert(END, self.user.username + ': ' + messageContent + '\n')

    toSend = {}

    if len(message_content) > 0 and message_content[0] == '!':
      toSend = { 'username' : self.user.username, 'language' : 'en', 'message' : message_content, 'translate' : False  }
      self.tcp.send(json.dumps(toSend).encode('utf-8'))
      
      command_interpreter = CommandInterpreter()
      newMessage = str(command_interpreter.interpretCommand(self.user, message_content[1:]))
      toSend = { 'username' : 'NEAR', 'language' : 'en', 'message' : newMessage, 'translate' : True  }
    else:
      toSend = { 'username' : self.user.username, 'language' : self.user.language, 'message' : message_content, 'translate' : True }

    self.tcp.send(json.dumps(toSend).encode('utf-8'))

    #self.messages.config(state=DISABLED)
    #self.messages.see(END)
    #self.message.delete(0, END)

  def logoff(self):
    self.changed_screen = True
    self.running = False
    self.tcp.send("{quit}".encode('utf-8'))
    self.tcp.close()
    import gui.login
    self.next_screen = gui.login.Login(self.window)
    self.grid_forget()

  def quit(self):
    self.next_screen = None
    self.running = False
    self.tcp.send("{quit}".encode('utf-8'))
    self.tcp.close()
    self.window.destroy()
    exit()

  def center(self):
    self.window.update_idletasks()
    w = self.window.winfo_screenwidth()
    h = self.window.winfo_screenheight()
    size = tuple(int(_) for _ in self.window.geometry().split('+')[0].split('x'))
    x = w / 2 - size[0] / 2
    y = h / 2 - size[1] / 2
    self.window.geometry("%dx%d+%d+%d" % (size + (x, y)))

  def run(self):
    self.window.mainloop()
