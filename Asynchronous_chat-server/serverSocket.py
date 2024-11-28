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
            target_user = data.get("target_user")

            if action == "create_room":
                if room not in rooms:
                    rooms[room] = {"messages": [], "users": []}
                clientSocket.send(pickle.dumps({"status": "room_created"}))
            
            elif action == "create_private_room":
                private_room_name = f"{user}_{target_user}_private"
                if private_room_name not in rooms:
                    rooms[private_room_name] = {"messages": [], "users": [user, target_user]}
                clientSocket.send(pickle.dumps({"status": "private_room_created", "room_name": private_room_name}))

            elif action == "get_rooms":
                accessible_rooms = [room_name for room_name, room_data in rooms.items()
                                    if "private" not in room_name or user in room_data["users"]]
                clientSocket.send(pickle.dumps({"rooms": accessible_rooms}))

            elif action == "send_message":
                if room in rooms and (user in rooms[room]["users"] or "private" not in room):
                    rooms[room]["messages"].append((user, message))
                    clientSocket.send(pickle.dumps({"status": "message_sent"}))

            elif action == "get_messages":
                if room in rooms and (user in rooms[room]["users"] or "private" not in room):
                    clientSocket.send(pickle.dumps({"messages": rooms[room]["messages"]}))
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
    print("Server started...")

    while True:
        clientSocket, addr = server.accept()
        print(f"New connection: {addr}")
        clientHandler = threading.Thread(target=handleClient, args=(clientSocket,))
        clientHandler.start()

if __name__ == "__main__":
    startServer()
