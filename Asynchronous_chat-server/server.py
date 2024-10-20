import asyncio
import pickle

rooms = {}

async def handleClient(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Клиент подключился: {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                print(f"Клиент {addr} отключился.")
                break

            try:
                request = pickle.loads(data)
            except Exception as e:
                print(f"Ошибка при десериализации данных: {e}")
                continue

            action = request.get("action")
            room = request.get("room")
            user = request.get("user")
            message = request.get("message")

            if action == "create_room":
                if room not in rooms:
                    rooms[room] = []
                response = pickle.dumps({"status": "room_created"})
                writer.write(response)
                await writer.drain()

            elif action == "get_rooms":
                response = pickle.dumps({"rooms": list(rooms.keys())})
                writer.write(response)
                await writer.drain()

            elif action == "send_message":
                if room in rooms:
                    rooms[room].append((user, message))
                    response = pickle.dumps({"status": "message_sent"})
                    writer.write(response)
                    await writer.drain()

            elif action == "get_messages":
                if room in rooms:
                    response = pickle.dumps({"messages": rooms[room]})
                else:
                    response = pickle.dumps({"messages": []})
                writer.write(response)
                await writer.drain()

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Соединение с клиентом {addr} закрыто.")

async def main():
    server = await asyncio.start_server(handleClient, "0.0.0.0", 5555)
    print("Сервер запущен...")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
