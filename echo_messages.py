#!/usr/bin/env python3

"""
This script echoes all messages it receives.

To work properly, the botdir folder must contain a login.json file with the login information (homeserver, user_id, device_id, access_token) and the store folder of the AsyncClient.
This folder can be prepared and verified with the create_bot_dir.py script:
https://github.com/gratach/create-matrix-nio-bot-dir/blob/52c5d79e2e63e301a946822a080f2bdc5acb36a3/create_bot_dir.py
"""

import asyncio
from pathlib import Path
from nio import AsyncClient, AsyncClientConfig, RoomMessageText
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
    await client.sync(full_state=True) # full_state=True is necessary or else a bug occurs (see message_to_all_rooms_bug.py)

    async def message_cb(room, event):
        if event.sender != client.user_id and event.body:
            await client.room_send(
                room_id=room.room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": f"I received '{event.body}'",
                }
            )

    # Add the message callback
    client.add_event_callback(message_cb, RoomMessageText)

    # Wait for the client to receive messages
    await client.sync_forever(timeout=30000) # timeout in milliseconds

asyncio.run(main())