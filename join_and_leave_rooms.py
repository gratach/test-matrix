#!/usr/bin/env python3

"""
This script joins all rooms the bot is invited to and leaves all rooms where the bot is the only member.

The botdir folder contains the login.json file with the login information (homeserver, user_id, device_id, access_token) and the store folder of the AsyncClient.
It can be prepared and verified with the create_bot_dir.py script:
https://github.com/gratach/create-matrix-nio-bot-dir/blob/ac12df13a8203c6289401296a7dcebae5da8842e/create_bot_dir.py
"""

import asyncio
from pathlib import Path
from nio import AsyncClient, AsyncClientConfig, JoinError, RoomMemberEvent, InviteMemberEvent
from json import load
from aioconsole import ainput

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
    resp = await client.sync()

    # Iterate over all invitations that were received since the last time the bot was running
    # Invatations that were received before or during the last run are not listed
    for room_id in client.invited_rooms.keys():
        try:
            # Join the room
            resp = await client.join(room_id)
            # Check if the response is a nio.responses.JoinError:
            if isinstance(resp, JoinError):
                raise Exception("Failed to join room")
        except Exception as e:
            # Leave the room if joining failed
            resp = await client.room_leave(room_id)

    # Iterate over all joined rooms
    for room_id in (await client.joined_rooms()).rooms:
        # Get all members in the room
        members = (await client.joined_members(room_id)).members
        # If I am the only member, leave the room
        if len(members) == 1:
            await client.room_leave(room_id)

    # The callback functions to handle invites and member events

    async def on_invite(room, event):
        # If you are invited to a room
        if event.state_key == client.user_id:
            # Join the room
            try:
                resp = await client.join(room.room_id)
                if isinstance(resp, JoinError):
                    raise Exception("Failed to join room")
            except Exception as e:
                # Leave the room if joining failed
                resp = await client.room_leave(room.room_id)
    async def on_member_event(room, event):
        # If someone else leaves or is banned from the room
        if (event.membership == "leave" or event.membership == "ban") and event.state_key != client.user_id:
            # Get all members in the room
            members = (await client.joined_members(room.room_id)).members
            # If I am the only member, leave the room
            if len(members) == 1:
                await client.room_leave(room.room_id)

    # Add the callbacks
    client.add_event_callback(on_invite, (InviteMemberEvent,))
    client.add_event_callback(on_member_event, (RoomMemberEvent,))

    # Function to close the client with the command line
    async def wait_for_close():
        await ainput("Press enter to close the client")
        await client.close()
        print("It will take some time to close the client. Please wait...")
    
    # Function to sync the client forever
    async def sync_forever():
        try:
            await client.sync_forever(timeout=30000)
        except Exception as e:
            print(e)
            await client.close()

    # Sync until the client is closed
    await asyncio.gather(
        sync_forever(),
        wait_for_close()
        )

asyncio.run(main())
