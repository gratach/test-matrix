#!/usr/bin/env python3

"""
This script sends a message to all rooms the bot is in.

The botdir folder contains the login.json file with the login information (homeserver, user_id, device_id, access_token) and the store folder of the AsyncClient.
It can be prepared and verified with the create_bot_dir.py script:
https://github.com/gratach/create-matrix-nio-bot-dir/blob/ac12df13a8203c6289401296a7dcebae5da8842e/create_bot_dir.py
"""

import asyncio
from pathlib import Path
from nio import AsyncClient, AsyncClientConfig
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

    # Send message to all joined rooms
    # Strange error: In some cases, the room_send method raises an localProtocolError "No such room with id ... found"
    for room_id in rooms:
        await client.room_send(
            room_id,
            "m.room.message",
            {
                "msgtype": "m.text",
                "body": "Hi to all rooms",
            },
            ignore_unverified_devices=True,
        )

asyncio.run(main())