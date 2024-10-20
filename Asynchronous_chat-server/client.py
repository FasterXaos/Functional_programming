import asyncio
import tkinter as tk
from tkinter import simpledialog
import pickle


class ChatClient:
    def __init__(self, master):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.master = master
        self.master.title("Chat Client")

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

        self.createRoomButton = tk.Button(self.topFrame, text="Создать комнату", command=self.createRoom, state=tk.DISABLED)
        self.createRoomButton.pack(side=tk.LEFT)

        self.joinRoomButton = tk.Button(self.topFrame, text="Присоединиться", command=self.joinRoom, state=tk.DISABLED)
        self.joinRoomButton.pack(side=tk.LEFT)

        self.userLabel = tk.Label(self.topFrame, text=f"Пользователь: {self.username}")
        self.userLabel.pack(side=tk.LEFT, padx=10)

        self.roomLabel = tk.Label(self.topFrame, text="Текущая комната: None")
        self.roomLabel.pack(side=tk.LEFT, padx=10)

        self.loop.create_task(self.connectToServer())
        self.master.after(100, self.runAsyncioTasks)

        self.isUpdatingMessages = False

    async def connectToServer(self):
        try:
            self.reader, self.writer = await asyncio.open_connection("localhost", 5555)
            print("Подключение к серверу установлено.")
            self.createRoomButton.config(state=tk.NORMAL)
            self.joinRoomButton.config(state=tk.NORMAL)
        except ConnectionError:
            print("Не удалось подключиться к серверу.")
        
        self.loop.create_task(self.fetchRooms())

    def runAsyncioTasks(self):
        try:
            self.loop.stop()
            self.loop.run_forever()
        except Exception as e:
            print(f"Ошибка в asyncio: {e}")
        finally:
            self.master.after(100, self.runAsyncioTasks)

    def updateRoomList(self):
        self.loop.create_task(self.fetchRooms())

    async def fetchRooms(self):
        request = {"action": "get_rooms"}
        self.writer.write(pickle.dumps(request))
        await self.writer.drain()

        response = await self.reader.read(1024)
        if response:
            data = pickle.loads(response)
            rooms = data.get("rooms", [])
            self.roomList.delete(0, tk.END)
            for room in rooms:
                self.roomList.insert(tk.END, room)

    def createRoom(self):
        roomName = simpledialog.askstring("Новая комната", "Введите название комнаты:")
        if roomName:
            print(f"Создание новой комнаты: {roomName}")
            self.loop.create_task(self.sendCreateRoomRequest(roomName))

    async def sendCreateRoomRequest(self, roomName):
        request = {"action": "create_room", "room": roomName}
        self.writer.write(pickle.dumps(request))
        await self.writer.drain()

        response = await self.reader.read(1024)
        if response:
            data = pickle.loads(response)
            if data.get("status") == "room_created":
                print(f"Комната '{roomName}' создана.")
                self.updateRoomList()

    def joinRoom(self):
        selectedRoom = self.roomList.get(tk.ACTIVE)
        if selectedRoom:
            self.currentRoom = selectedRoom
            self.roomLabel.config(text=f"Текущая комната: {self.currentRoom}")
            self.messageBox.config(state=tk.NORMAL)
            self.messageBox.delete(1.0, tk.END)
            self.messageBox.config(state=tk.DISABLED)
            self.loop.create_task(self.updateMessages())

    async def updateMessages(self):
        if self.isUpdatingMessages:
            return
        self.isUpdatingMessages = True

        try:
            if self.currentRoom:
                request = {"action": "get_messages", "room": self.currentRoom}
                self.writer.write(pickle.dumps(request))
                await self.writer.drain()

                response = await self.reader.read(1024)
                if response:
                    data = pickle.loads(response)
                    messages = data.get("messages", [])

                    self.messageBox.config(state=tk.NORMAL)
                    self.messageBox.delete(1.0, tk.END)
                    for user, msg in messages:
                        self.messageBox.insert(tk.END, f"{user}: {msg}\n")
                    self.messageBox.config(state=tk.DISABLED)
                    self.messageBox.see(tk.END)

        finally:
            self.isUpdatingMessages = False

        self.master.after(100, lambda: self.loop.create_task(self.updateMessages()))

    def sendMessage(self, event=None):
        message = self.inputMessage.get()
        if self.currentRoom and message:
            self.loop.create_task(self.sendChatMessage(message))
            self.inputMessage.delete(0, tk.END)

    async def sendChatMessage(self, message):
        request = {"action": "send_message", "room": self.currentRoom, "user": self.username, "message": message}
        self.writer.write(pickle.dumps(request))
        await self.writer.drain()

        response = await self.reader.read(1024)
        if response:
            data = pickle.loads(response)
            if data.get("status") == "message_sent":
                await self.updateMessages()


if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
