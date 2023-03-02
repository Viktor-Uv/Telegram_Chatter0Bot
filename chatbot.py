import openai, telebot, json
from openai.error import OpenAIError

# Set up Telegram Bot credentials
bot = telebot.TeleBot("5915763807:AAGEed0Vh--bSqpuiNqO3BoiwIg24xH9OI0")
# Set up OpenAI API credentials
openai.api_key = "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"
# Define default parameters
DEF_TEMP = 0.5
MAX_DIALOG_SIZE = 5
MIN_CHARACTERS = 250
# Load existing user data from file
try:
    # Read the JSON object
    with open('data.json', 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}


def write_data():
    with open('data.json', 'w') as f:
        json.dump(data, f)


@bot.message_handler(commands=['temp'])
def set_temperature(message):
    # Take ID of a group or person
    id = str(message.chat.id)
    # Initialise new id, if it doesn't exist
    initialise(id, message)
    # If empty parameter given - show current set value
    if len(message.text.split()) == 1:
        bot.reply_to(message, f"""Parameter "temperature" is currently set to {data[id]["Temp"]}""")
    else:
        # Extract parameter from the message
        try:
            data[id]["Temp"] = float(message.text.split()[1])
        except:
            # Remind proper usage example
            bot.reply_to(message, """Usage: "/temp temperature" (0 to 1)""")
            return
        temp = data[id]["Temp"]
        # Check usage
        if temp >= 0 and temp <= 1:
            # Indicate success
            bot.reply_to(message, f"""Parameter "temperature" is now set to {temp}""")
        else:
            # Indicate usage error
            bot.reply_to(message, """Usage: "/temp temperature" (number from 0 to 1)""")
    # Update data file
    write_data()


# Function to generate response using OpenAI API
def generate_response(message, id):
    # Generate AI responce
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=message,
            temperature=data[id]["Temp"],
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.5
        )
    except OpenAIError as e:
        error_message = "Error occured: " + str(e)
        return error_message

    # Return AI generated reply
    return response.choices[0].text


# Clears bot's memory
@bot.message_handler(commands=['clear'])
def send_welcome(message):
    # Take ID of a group or person
    id = str(message.chat.id)
    data[id]["Dialog"] = ""
    bot.reply_to(message, "Memory erased.")
    # Update data file
    write_data()

@bot.message_handler(commands=['start'])
def send_start(message):
    bot.reply_to(message, "Hello, I'm your new bot!")


@bot.message_handler(commands=['hello'])
def greet_user(message):
    # Get the user's first name
    first_name = message.from_user.first_name
    # Greet the user by name or with a default message if the first name can't be retrieved
    if first_name:
        bot.reply_to(message, f"Hello, {first_name}!")
    else:
        bot.reply_to(message, "Hello there!")


@bot.message_handler(commands=['help'])
def help_user(message):
    # Print brief help
    bot.reply_to(message, f"""Reply to my message with any text to get an AI response\n
Use "/temp number" to set the "temperature" (between 0 and 1, default {DEF_TEMP}). """ + \
"""Higher values will make the output more random, while lower values will make it more """ + \
"""focused and deterministic. Using without parameter will display the "temperature" currently set\n
Use "/clear" to clear Bot's memory\n
Use "/start" for a welcome message\n
Use "/hello" to be greeted""")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    # Take ID of a person and initialise, then increment the request count
    id = str(message.from_user.id)
    initialise(id, message)
    data[id]["AI_Requests"] += 1
    # Take ID of a group or person and rewrite the above person ID
    id = str(message.chat.id)
    initialise(id, message)
    # Reply to the chat
    dialog = build_dialog(message, id)
    response = generate_response(dialog, str(message.chat.id))
    bot.reply_to(message, response)
    # Save dialog
    dialog += shorten(response)
    data[id]["Dialog"] = dialog
    # Update data file
    write_data()


# Generate dialog of the MAX_DIALOG_SIZE from the past requests
def build_dialog(message, id):
    # Get the current dialog
    dialog = data[id]["Dialog"].split('\n\n')
    if dialog == ['']:
        return shorten(message.text) + '\n'
    # If the dialog size exceeds the maximum, remove the oldest request/response pair
    if len(dialog) >= MAX_DIALOG_SIZE:
        dialog.pop(0)
    # Add the new request
    dialog.append(shorten(message.text))
    # Generate the response
    dialog = '\n\n'.join(dialog)
    return dialog + '\n'


def shorten(text):
    shortened = ""
    for i in range(len(text)):
        if i > MIN_CHARACTERS and text[i] in ['.', '?', '!']:
            shortened += text[i]
            break
        else:
            shortened += text[i]
    return shortened


def initialise(id, message):
    if id not in data:
        if int(id) >= 0:
            nickname = message.from_user.username
            data[id] = {
                "User_name": message.from_user.full_name,
                "Nick": "" if nickname is None else nickname,
                "Dialog": "",
                "Temp": DEF_TEMP,
                "AI_Requests": 0
            }
        else:
            chat_info = bot.get_chat(id)
            data[id] = {
                "Group_name": chat_info.title,
                "Dialog": "",
                "Temp": DEF_TEMP
            }


bot.polling()
