#!/usr/bin/env python3

"""
This script asks the user if it should send a message to all joined rooms.

To work properly, the botdir folder must contain a login.json file with the login information (homeserver, user_id, device_id, access_token) and the store folder of the AsyncClient.
This folder can be prepared and verified with the create_bot_dir.py script:
https://github.com/gratach/create-matrix-nio-bot-dir/blob/ac12df13a8203c6289401296a7dcebae5da8842e/create_bot_dir.py

A verry strange bug can be observed:
When this script is executed and the user chooses not to send a message, something gets broken.
When the script is executed again and the user chooses to send a message, the LocalProtocolError "No such room with id ... found" is raised for all rooms.
Now if something gets written in one of the rooms, the error disappears for this room and the script works as expected.
The script can be executed multiple times without any problems as long as the user chooses to send a message.
When the user chooses not to send a message, the error appears again on the next execution.
"""

import asyncio
from pathlib import Path
from nio import AsyncClient, AsyncClientConfig, LocalProtocolError
from json import load

BOTDIR = Path(__file__).parent / "botdir"
LOGIN = BOTDIR / "login.json"
STORE = BOTDIR / "store"

async def main():

    # Configuration options for the AsyncClient
    config = AsyncClientConfig(
        max_limit_exceeded=0,
        max_timeouts=0,
        store_sync_tokens=True,
        encryption_enabled=True,
    )

    # Load login info from login.json
    with LOGIN.open() as f:
        login_info = load(f)

    # Create a new AsyncClient
    client = AsyncClient(
        login_info["homeserver"],
        login_info["user_id"],
        device_id=login_info["device_id"],
        store_path=STORE,
        config=config,
    )
    client.user_id = login_info["user_id"]
    client.access_token = login_info["access_token"]

    # Load the stored sync tokens
    client.load_store()

    # Upload keys if necessary
    if client.should_upload_keys:
        await client.keys_upload()

    # Syncronize with the server
    await client.sync()

    # Get all joined rooms
    rooms = (await client.joined_rooms()).rooms

    if input("Do you want to send messages to all rooms? (y/n) ") == "y":

        # Send message to all joined rooms
        for room_id in rooms:
            try:
                await client.room_send(
                    room_id,
                    "m.room.message",
                    {
                        "msgtype": "m.text",
                        "body": "Hi to all rooms!",
                    },
                    ignore_unverified_devices=True,
                )
            except LocalProtocolError as e:
                print("No message could be sent to room", room_id)
                print("Error: " + " ".join(e.args))
    
    await client.close()

asyncio.run(main())