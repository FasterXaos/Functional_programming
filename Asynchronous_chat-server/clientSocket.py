import socket
import tkinter as tk
from tkinter import simpledialog
import pickle


class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Chat Client")
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 5555))
        
        self.username = simpledialog.askstring("Имя пользователя", "Введите ваше имя:")
        
        self.mainFrame = tk.Frame(self.master)
        self.mainFrame.pack(fill=tk.BOTH, expand=True)
        
        self.leftFrame = tk.Frame(self.mainFrame)
        self.leftFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        
        self.rightFrame = tk.Frame(self.mainFrame)
        self.rightFrame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.topFrame = tk.Frame(self.master)
        self.topFrame.pack(side=tk.TOP, fill=tk.X)

        self.roomList = tk.Listbox(self.leftFrame, width=30)
        self.roomList.pack(fill=tk.BOTH, expand=True)

        self.messageBox = tk.Text(self.rightFrame, state=tk.DISABLED, height=20)
        self.messageBox.pack(fill=tk.BOTH, expand=True)

        self.inputMessage = tk.Entry(self.rightFrame)
        self.inputMessage.pack(fill=tk.X)
        self.inputMessage.bind("<Return>", self.sendMessage)

        self.createRoomButton = tk.Button(self.topFrame, text="Создать комнату", command=self.createRoom)
        self.createRoomButton.pack(side=tk.LEFT)

        self.joinRoomButton = tk.Button(self.topFrame, text="Присоединиться", command=self.joinRoom)
        self.joinRoomButton.pack(side=tk.LEFT)

        self.userLabel = tk.Label(self.topFrame, text=f"Пользователь: {self.username}")
        self.userLabel.pack(side=tk.LEFT, padx=10)

        self.roomLabel = tk.Label(self.topFrame, text="Текущая комната: None")
        self.roomLabel.pack(side=tk.LEFT, padx=10)

        self.currentRoom = None
        self.updateRoomList()
    
    def updateRoomList(self):
        request = {"action": "get_rooms"}
        self.socket.send(pickle.dumps(request))
        
        response = pickle.loads(self.socket.recv(1024))
        rooms = response.get("rooms", [])
        
        self.roomList.delete(0, tk.END)
        for room in rooms:
            self.roomList.insert(tk.END, room)

        self.master.after(1000, self.updateRoomList)
    
    def createRoom(self):
        roomName = simpledialog.askstring("Новая комната", "Введите название комнаты:")
        if roomName:
            request = {"action": "create_room", "room": roomName}
            self.socket.send(pickle.dumps(request))
            response = pickle.loads(self.socket.recv(1024))
            if response.get("status") == "room_created":
                self.updateRoomList()

    def joinRoom(self):
        selectedRoom = self.roomList.get(tk.ACTIVE)
        if selectedRoom:
            self.currentRoom = selectedRoom
            self.roomLabel.config(text=f"Текущая комната: {self.currentRoom}")
            self.messageBox.config(state=tk.NORMAL)
            self.messageBox.delete(1.0, tk.END)
            self.messageBox.config(state=tk.DISABLED)
            self.updateMessages()
    
    def updateMessages(self):
        if self.currentRoom:
            request = {"action": "get_messages", "room": self.currentRoom}
            self.socket.send(pickle.dumps(request))
            response = pickle.loads(self.socket.recv(1024))
            messages = response.get("messages", [])
            
            self.messageBox.config(state=tk.NORMAL)
            self.messageBox.delete(1.0, tk.END)
            for user, msg in messages:
                self.messageBox.insert(tk.END, f"{user}: {msg}\n")
            self.messageBox.config(state=tk.DISABLED)

        self.master.after(1000, self.updateMessages)

    def sendMessage(self, event=None):
        message = self.inputMessage.get()
        if self.currentRoom and message:
            request = {"action": "send_message", "room": self.currentRoom, "user": self.username, "message": message}
            self.socket.send(pickle.dumps(request))
            response = pickle.loads(self.socket.recv(1024))
            if response.get("status") == "message_sent":
                self.inputMessage.delete(0, tk.END)
                self.updateMessages()


if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
