from nio import AsyncClient
from pathlib import Path
from aioconsole import ainput
import json
import asyncio
import nio

# Load login info from login.json
loginFile = Path(__file__).parent / "login.json"
if not loginFile.exists():
    loginFile.write_text('{"homeserver": "https://matrix.org", "username": "username", "password": "password"}')
loginInfo = json.loads(loginFile.read_text())

# Load the current batch from batch.txt
batchFile = Path(__file__).parent / "batch.txt"
if not batchFile.exists():
    batchFile.write_text("")
currentBatch = batchFile.read_text()

continueLoop = True

async def invite(*args, **kwargs):
    print("invite...")

async def message_callback(*args, **kwargs):
    print("message...")
    

async def main():
    # Create a new AsyncClient and login
    config = nio.AsyncClientConfig(
        max_limit_exceeded=0,
        max_timeouts=0,
        store_sync_tokens=True,
        encryption_enabled=True
    )
    client = AsyncClient(loginInfo["homeserver"], loginInfo["username"], config = config)
    await client.login(loginInfo["password"])
    # Sync the client
    await client.sync()
    # Accept all invitations
    for room_id in client.invited_rooms.keys():
        try:
            resp = await client.join(room_id)
            # Check if the response is a nio.responses.JoinError:
            if isinstance(resp, nio.responses.JoinError):
                raise Exception("Failed to join room")
            print(resp)
        except Exception as e:
            resp = await client.room_leave(room_id)
            print(e)
        #await client.join(room_id)
    
    # Receive messages
    client.add_event_callback(invite, nio.InviteEvent)
    client.add_event_callback(message_callback, nio.RoomMessageText)
    if client.should_upload_keys:
        await client.keys_upload()
    await client.room_send(
        room_id="!FEmFIVcqWoAfqSqPlV:matrix.org",
        message_type="m.room.message",
        content={"msgtype": "m.text", "body": "Hi, world!"},
    )

    
    res = await client.sync(timeout=300000)
    print(res)


asyncio.run(main())