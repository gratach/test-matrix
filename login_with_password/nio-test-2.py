import asyncio
import json
from pathlib import Path

from nio import AsyncClient, MatrixRoom, RoomMessageText

# Load login info from login.json
loginFile = Path(__file__).parent / "login.json"
if not loginFile.exists():
    loginFile.write_text('{"homeserver": "https://matrix.org", "username": "username", "password": "password"}')
loginInfo = json.loads(loginFile.read_text())


async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    print(
        f"Message received in room {room.display_name}\n"
        f"{room.user_name(event.sender)} | {event.body}"
    )


async def main() -> None:
    client = AsyncClient(loginInfo["homeserver"], loginInfo["username"])
    client.add_event_callback(message_callback, RoomMessageText)

    print(await client.login(loginInfo["password"]))
    # "Logged in as @alice:example.org device id: RANDOMDID"

    # If you made a new room and haven't joined as that user, you can use
    # await client.join("your-room-id")

    await client.sync_forever(timeout=30000)  # milliseconds


asyncio.run(main())