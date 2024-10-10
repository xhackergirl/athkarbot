import logging
import random
import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.types import PeerChannel, PeerChat
from db import (
    setup_database,
    save_channel_data,
    get_channel_data,
    fetch_last_channel_group,
    fetch_channel_phrases,
    fetch_channel_data_phrases,
    fetch_channel_data_frequency,
    fetch_channel_group_id,
    delete_channel_data,
    fetch_channel_data,
    fetch_all_channels,
    fetch_channel_group_name
)
setup_database()

# Configuration
API_ID = 
API_HASH = 
BOT_TOKEN =

# Logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States
SELECTING_ACTION, FORWARD_CHANNEL_GROUP, SETTING_PHRASES, SETTING_FREQUENCY, LIST_CHANNELS, EDIT_SELECTION, EDIT_PHRASES, EDIT_FREQUENCY = range(8)

# Data Structures
user_data = {}  # user_id: {channels: {channel_id: {'phrases': [], 'frequency': int}}, 'state': state, 'edit_channel': channel_id}
scheduled_tasks = {}
channels_groups = {}
default_phrases = {}
# Initialize Client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Buttons
def main_menu():
    return [
        [Button.inline("Add Channel/Group", data="add")],
        [Button.inline("List Channels/Groups", data="list")],
        [Button.inline("Help", data="help")],
    ]

def back_button():
    return [Button.inline("Back", data="back")]

def edit_menu(channel_id):
    return [
        [Button.inline("Edit Phrases", data=f"edit_phrases")],
        [Button.inline("Edit Frequency", data=f"edit_frequency")],
        [Button.inline("Delete Channel/Group", data=f"delete")],
        [Button.inline("Back", data="back")]
    ]


# Handlers
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    if user_id not in user_data:
        user_data[user_id] = {'channels': {}}
    user_data[user_id]['state'] = SELECTING_ACTION
    
    await event.respond("Welcome! Choose an action:", buttons=main_menu())

@client.on(events.NewMessage(pattern='/help'))
async def help_cmd(event):
    help_text = "Use the buttons to manage your channels/groups.\n- Forward/Add to set up.\n- List to view/edit."
    await event.respond(help_text, buttons=back_button())

@client.on(events.NewMessage(pattern='/stop'))
async def stop(event):
    user_id = event.sender_id
    user_data[user_id]['state'] = SELECTING_ACTION
    await event.respond("Operation cancelled.", buttons=main_menu())

async def send_message(channel_id, message):
    # Store the message in channels_groups for comparison
    if channel_id not in channels_groups:
        channels_groups[channel_id] = {'last_message_id': None, 'last_content': None}
        
    # If there is a last message, delete it
    if channels_groups[channel_id]['last_message_id']:
        try:
            await client.delete_message(channel_id, channels_groups[channel_id]['last_message_id'])
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    # Send the new message
    sent_message = await client.send_message(channel_id, message)
    
    # Store the last message ID and content
    channels_groups[channel_id]['last_message_id'] = sent_message.id
    channels_groups[channel_id]['last_content'] = message

async def edit_message_if_needed(channel_id, new_content):
    if channel_id in channels_groups:
        last_content = channels_groups[channel_id]['last_content']
        if last_content != new_content:  # Only edit if the content has changed
            await client.edit_message(channel_id, channels_groups[channel_id]['last_message_id'], new_content)
            channels_groups[channel_id]['last_content'] = new_content  # Update the last content
        else:
            logger.info("No changes detected, not editing the message.")


@client.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    if user_id not in user_data:
        user_data[user_id] = {
            'state': SELECTING_ACTION,
            'channels': {}
        }
    state = user_data[user_id].get('state', SELECTING_ACTION)

    if data == "forward" or data == "add":
        user_data[user_id]['state'] = FORWARD_CHANNEL_GROUP
        await event.edit("Forward a post from your channel or group to extract the ID.", buttons=back_button())

    if data == "use_default_phrases":
        # Use default phrases
        default_phrases = [
        "- سُبْحَانَ اللَّهِ وَبِحَمْدِهِ",
        "- لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ، وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ",
        "- الْحَمْدُ لِلَّهِ",
        "- يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ أَصْلِحْ لِي شَأْنِي كُلَّهُ وَلَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ",
        "- لَا إِلَهَ إِلَّا اللَّهُ",
        "- حَسْبِيَ اللَّهُ وَنِعْمَ الْوَكِيلُ",
        "- اللَّهُ أَكْبَرُ",
        "- اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنَّا",
        "- بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ",
        "- لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ",
        "- أَسْتَغْفِرُ اللَّهَ",
        "- لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ",
        "- اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَى نَبِيِّنَا مُحَمَّدٍ",
        "- سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
        "- رَبِّ اغْفِرْ لِي وَتُبْ عَلَيَّ إِنَّكَ أَنْتَ التَّوَّابُ الرَّحِيمُ",
        "- اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ",
        "- رَبِّ اغْفِرْ لِي وَلِوَالِدَيَّ وَلِلْمُؤْمِنِينَ يَوْمَ يَقُومُ الْحِسَابُ"
            ]
        user_data[user_id]['phrases'] = default_phrases
        
        await event.edit(f"Default phrases set: {', '.join(default_phrases)}")
        user_data[user_id]['state'] = SETTING_FREQUENCY
        await event.respond("Set frequency (times per day):", buttons=back_button())
    
    elif data == "use_default_phrases_2":
        # Use default phrases
        default_phrases = [
        "- سُبْحَانَ اللَّهِ وَبِحَمْدِهِ",
        "- لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ، وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ",
        "- الْحَمْدُ لِلَّهِ",
        "- يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ أَصْلِحْ لِي شَأْنِي كُلَّهُ وَلَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ",
        "- لَا إِلَهَ إِلَّا اللَّهُ",
        "- حَسْبِيَ اللَّهُ وَنِعْمَ الْوَكِيلُ",
        "- اللَّهُ أَكْبَرُ",
        "- اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنَّا",
        "- بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ",
        "- لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ",
        "- أَسْتَغْفِرُ اللَّهَ",
        "- لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ",
        "- اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَى نَبِيِّنَا مُحَمَّدٍ",
        "- سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
        "- رَبِّ اغْفِرْ لِي وَتُبْ عَلَيَّ إِنَّكَ أَنْتَ التَّوَّابُ الرَّحِيمُ",
        "- اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ",
        "- رَبِّ اغْفِرْ لِي وَلِوَالِدَيَّ وَلِلْمُؤْمِنِينَ يَوْمَ يَقُومُ الْحِسَابُ"
            ]
        user_data[user_id]['phrases'] = default_phrases
        
        await event.edit(f"Default phrases set: {', '.join(default_phrases)}", buttons=back_button())
        

    elif data == "list":
        user_data[user_id]['state'] = LIST_CHANNELS
        channels = get_channel_data(user_id)
        if channels:
            buttons = [[Button.inline(f"{channel_id[3]}", data=f"eedit_{channel_id[0]}") for channel_id in channels]]
            buttons.append(back_button())
            await event.edit("Choose a channel/group to edit:", buttons=buttons)
        else:
            await event.edit("No channels/groups found. Forward a post to add one.", buttons=main_menu())

    elif data.startswith("eedit_"):
        channel_id = data.split("_")[1]
        user_data[user_id]['state'] = EDIT_SELECTION
        user_data[user_id]['edit_channel'] = channel_id
        await event.edit(f"Editing channel/group `{channel_id}`. Choose an action:", buttons=edit_menu(channel_id))
    
    elif data == "edit_phrases":
        user_data[user_id]['state'] = EDIT_PHRASES
        channel_group_id = fetch_channel_group_id(user_id)
        phrases = fetch_channel_data_phrases(user_id, channel_group_id)['phrases']
        phrases = f"\n".join(phrases.split(","))
        buttons = [
                [Button.inline("Use Default Phrases", b"use_default_phrases_2")],
                [Button.inline("Back", b"back")]
                ]
        await event.respond(f"here are your current phrases {phrases} \nEnter new phrases (comma-separated) or choose default: ", parse_mode='markdown', buttons=buttons)
        
    elif data == "edit_frequency":
        user_data[user_id]['state'] = EDIT_FREQUENCY
        await event.edit("Enter new frequency (times per day):", buttons=back_button())

    elif data == "delete":  # When the delete button is pressed
        # Here is where you will replace the old channel group ID fetching
        channel_group_id = fetch_channel_group_id(user_id)
        name = fetch_channel_group_name(channel_group_id)
        if channel_group_id is None:
            await event.respond("No channel/group found. Please add one first.", buttons=main_menu())
            return

        await event.respond(f"Are you sure you want to delete the channel/group `{name}`? (Yes/No)", buttons=[
            [Button.inline("Yes", data=f"confirm_delete_{channel_group_id}"), Button.inline("No", data="cancel_delete")]
        ])
    
    elif data.startswith("confirm_delete_"):  # Handle confirmation for deletion
        channel_group_id = data.split("_")[2]
        name = fetch_channel_group_name(channel_group_id)
        delete_channel_data(user_id, channel_group_id)
        await event.respond(f"Channel/Group `{name}` has been deleted.", buttons=main_menu())
    
    elif data == "cancel_delete":
        await event.respond("Deletion canceled.", buttons=main_menu())
    elif data == "help":
        help_text = "Use the buttons to manage your channels/groups.\n- Forward/Add to set up.\n- List to view/edit."
        await event.edit(help_text, buttons=back_button())
    elif data == "back":
        user_data[user_id]['state'] = SELECTING_ACTION
        await event.edit("Choose an action:", buttons=main_menu())
    else:
        await event.answer("Unknown action.", alert=True)

phrases = []

@client.on(events.NewMessage)
async def handle_messages(event):
    user_id = event.sender_id
    state = user_data[user_id].get('state', SELECTING_ACTION)
    
    if state == FORWARD_CHANNEL_GROUP:

        if event.message.fwd_from:
            phrases = ''
            frequency = 0
            channel_group_id = event.forward.chat.id
            name = event.forward.chat.title
            
            save_channel_data(user_id, channel_group_id, name, phrases, frequency, None, None)
            user_data[user_id]['channel_group_id'] = channel_group_id
            user_data[user_id]['channel_group_name'] = name
            user_data[user_id]['state'] = SETTING_PHRASES
            buttons = [
                [Button.inline("Use Default Phrases", b"use_default_phrases")],
                [Button.inline("Back", b"back")]
                ]
            await event.respond(f"Channel/Group `{name}` added. Enter phrases (comma-separated) or choose default: ", parse_mode='markdown', buttons=buttons)
        else:
            await event.respond("Please forward a valid channel or group post.", buttons=back_button())
    
    elif state == SETTING_PHRASES:
        # Split and strip the phrases entered by the user
        
        phrases = [p.strip() for p in event.message.text.split(',') if p.strip()]
        user_data[user_id]['phrases'] = phrases
        # Validate that at least one phrase is entered
        if not phrases:
            await event.respond("Enter at least one phrase (comma-separated):", buttons=back_button())
            return
        
        user_data[user_id]['state'] = SETTING_FREQUENCY
        await event.respond("Set frequency (times per day):", buttons=back_button())

    elif state == SETTING_FREQUENCY:
        try:
            frequency = int(event.message.text)
            
            if frequency <= 0:
                raise ValueError
        except:
            await event.respond("Enter a valid positive integer for frequency:", buttons=back_button())
            return
        user_data[user_id]['frequency'] = frequency
        phrases = user_data[user_id]['phrases']
        channel_group_id = user_data[user_id]['channel_group_id']
        name= user_data[user_id]['channel_group_name']
        delete_channel_data(user_id, channel_group_id)
        save_channel_data(user_id, channel_group_id, name, ','.join(phrases), frequency, None, None)
        
        user_data[user_id]['state'] = SELECTING_ACTION
        await event.respond(f"Frequency set to {frequency} times/day. the sending process will start in a minute", buttons=main_menu())
        #send message to the group/ channele
        await load_scheduled_tasks(channel_group_id)

    elif state == LIST_CHANNELS:
        channel_id = fetch_channel_group_id(user_id)
        channel_name = fetch_channel_group_name(channel_id)
        user_data[user_id]['state'] = EDIT_SELECTION
        await event.respond(f"Choose an option for channel/group `{channel_name}`:", buttons=edit_menu(channel_id))


    elif state == EDIT_SELECTION:
        if data == "edit_phrases":
            user_data[user_id]['state'] = EDIT_PHRASES
            buttons = [
                [Button.inline("Use Default Phrases", b"use_default_phrases")],
                [Button.inline("Back", b"back")]
                ]
            await event.respond(f"Channel/Group `{name}` added. Enter phrases (comma-separated) or choose default: ", parse_mode='markdown', buttons=buttons)
        
        elif data == "edit_frequency":
            user_data[user_id]['state'] = EDIT_FREQUENCY
            await event.respond("Enter new frequency (times per day):", buttons=back_button())
        else:
            await event.answer("Unknown action.", alert=True)


    elif state == EDIT_PHRASES:
        phrases = [p.strip() for p in event.message.text.split(',') if p.strip()]
        if not phrases:
            await event.respond("Enter at least one phrase (comma-separated):", buttons=back_button())
            return
        channel_group_data = fetch_last_channel_group(user_id)
        
        # If no channel/group is found in the database, notify the user
        if not channel_group_data:
            await event.respond("No channels/groups found to set phrases for. Please add a channel first.", buttons=main_menu())
            return
        
        channel_group_id = fetch_channel_group_id(user_id)
        name = fetch_channel_group_name(channel_group_id)
        
        # Save channel data to the database after adding
        existing_data = fetch_channel_data_frequency(user_id, channel_group_id)
        frequency = existing_data['frequency']
        user_data[user_id]['phrases'] = phrases
        delete_channel_data(user_id, channel_group_id)
        save_channel_data(user_id, channel_group_id, name, ','.join(phrases), frequency, None, None)
       
        user_data[user_id]['state'] = EDIT_SELECTION
        await event.respond(f"Phrases updated for channel/group `{name}`.", buttons=edit_menu(channel_group_id))

    elif state == EDIT_FREQUENCY:
        try:
            frequency = int(event.message.text)
            if frequency <= 0:
                raise ValueError
        except:
            await event.respond("Enter a valid positive integer for frequency:", buttons=back_button())
            return
        channel_group_data = fetch_last_channel_group(user_id)
        
        # If no channel/group is found in the database, notify the user
        if not channel_group_data:
            await event.respond("No channels/groups found to set frequency for. Please add a channel first.", buttons=main_menu())
            return
        
        channel_group_id = fetch_channel_group_id(user_id)
        name = fetch_channel_group_name(channel_group_id)
        
        # Save channel data to the database after adding
        existing_data = fetch_channel_data_phrases(user_id, channel_group_id)
        phrases = existing_data['phrases']
        delete_channel_data(user_id, channel_group_id)
        save_channel_data(user_id, channel_group_id, name, phrases, frequency, None, None)
        user_data[user_id]['state'] = EDIT_SELECTION
        await event.respond(f"Frequency updated for channel/group `{name}`.", buttons=edit_menu(channel_group_id))

async def load_scheduled_tasks(id):
    all_channels = fetch_all_channels()  # You need to implement this function
    if all_channels:
        for channel in all_channels:
            user_id = channel['user_id']
            channel_group_id = channel['channel_id']
            if int(channel_group_id) == id:
                print('Loading scheduled messages for user_id: {} and channel_group_id: {}' . format(user_id, channel_group_id))
                frequency = fetch_channel_data_frequency(user_id, channel_group_id)['frequency']
                interval = 24 / int(frequency) * 3600
                phrases = fetch_channel_data_phrases(user_id, channel_group_id)['phrases']
                phrases = phrases.split(',')
                first_phrases = [
                    "رَطِّبُوا أَلْسِنَتَكُمْ بِذِكْرِ اللَّـهِ:",
                    "وَعَنْ ذِكْرِ اللَّهِ لَا تَغْفُلُونَ:",
                    "لَا تَغْفلْ عَنْ ذِكْرِ اللَّهِ:",
                    "اذْكُرُوا اللَّهَ:"
                ]
                first_phrase = random.choice(first_phrases) # Randomly select 3 other phrases from the other_phrases list
                selected_phrases = random.sample(phrases, 3)
                message_text = f"{first_phrase}\n\n" + "\n".join(selected_phrases)
                message =str(message_text)

                try:
                    msg_id = fetch_channel_data_message_id(user_id, channel_group_id)['last_message_id']
                    await client.delete_messages(int('-100' + str(channel_group_id)), msg_id)
                except:
                    print('no previous message to delete')
                await asyncio.sleep(60)
                sent_message = await client.send_message(int('-100' + str(channel_group_id)), message)
                logger.info(f"Sent to {channel_group_id}: {message}")
                channel_name = fetch_channel_group_name(channel_group_id)
                phrases = fetch_channel_data_phrases(user_id, channel_group_id)['phrases']
                delete_channel_data(user_id, channel_group_id)
                save_channel_data(user_id, channel_group_id, channel_name, phrases, frequency, sent_message.id, sent_message.text)
                await asyncio.sleep(interval)
                await client.delete_messages(int('-100' + str(channel_group_id)), sent_message.id)
                

# Main entry point to start the client and load scheduled tasks
client.start() # Load any tasks that were previously scheduled
client.run_until_disconnected()
