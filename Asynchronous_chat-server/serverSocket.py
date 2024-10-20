import socket
import threading
import pickle

rooms = {}

def handleClient(clientSocket):
    while True:
        try:
            request = clientSocket.recv(1024)
            if not request:
                break

            data = pickle.loads(request)

            action = data.get("action")
            room = data.get("room")
            user = data.get("user")
            message = data.get("message")

            if action == "create_room":
                if room not in rooms:
                    rooms[room] = []
                clientSocket.send(pickle.dumps({"status": "room_created"}))
            
            elif action == "get_rooms":
                clientSocket.send(pickle.dumps({"rooms": list(rooms.keys())}))

            elif action == "send_message":
                if room in rooms:
                    rooms[room].append((user, message))
                    clientSocket.send(pickle.dumps({"status": "message_sent"}))

            elif action == "get_messages":
                if room in rooms:
                    clientSocket.send(pickle.dumps({"messages": rooms[room]}))
                else:
                    clientSocket.send(pickle.dumps({"messages": []}))
                    
        except Exception as e:
            print(f"Error: {e}")
            break
    
    clientSocket.close()

def startServer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5555))
    server.listen(5)
    print("Сервер запущен...")

    while True:
        clientSocket, addr = server.accept()
        print(f"Новое соединение: {addr}")
        clientHandler = threading.Thread(target=handleClient, args=(clientSocket,))
        clientHandler.start()


if __name__ == "__main__":
    startServer()
