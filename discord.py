import discord
from discord import Intents
from discord.ext import commands
import os
import asyncio
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tracemalloc
import json
import shlex

intents = discord.Intents.all()  
client = discord.Client(intents=intents)

path = r'/home/opc/trocan'
if not path.endswith('/'):
    path += '/'
CHANNEL_ID = 1112200552089124898  #log channel id
AVAILABLE_PARAMS = ['seedrand', 'seed', 'promptrand', 'default', 'verde']
PARAMS_DESC = {
    'seedrand': '\n\tThis parameter dictates if the seed is randomly generated or not. \n\n\tValues: \n\t\t0 = random \n\t\t1 = set to the "seed" parameter.',
    'seed': '\n\tThis parameter controls the seed for the random number generator. \n\n\tValues must be between 3 029 190 890 and 6 029 190 890.',
    'promptrand': '\n\tThis parameter toggles whether the prompt is the default, verde, or is chosen randomly from the parameter list. \n\n\tValues: \n\t\t0 = default \n\t\t1 = verde \n\t\t2 = random from list ',
    'default': '\n\tThis parameter sets the default prompt. \nThe prompt must be surrounded by "". \n\te.g.: -!sp default "dummy text 1"',
    'verde': '\n\tThis parameter sets the verde prompt. \nThe prompt must be surrounded by "". \n\te.g.: -!sp verde "dummy text 2"'
}
default_parameters = {
'seedrand': 0,
'seed': 3029190890,
'promptrand':0,
'default': "dummy text 1",
'verde': "dummy text 2"
}



#---------------Image and log---------------------
tracemalloc.start()
async def post_latest_image():
    path_to_watch = path  # your directory here
    list_of_files = os.listdir(path_to_watch) # list of files in the directory
    full_paths = [os.path.join(path_to_watch, i) for i in list_of_files if i.endswith(('.png', '.jpg', '.jpeg'))] # add here more extensions if needed

    latest_file = max(full_paths, key=os.path.getctime)  # latest created file in the directory
    print(f"Latest: {latest_file}")

    with open(latest_file, 'rb') as f:
        picture = discord.File(f)
        guild = discord.utils.get(client.guilds, id=449604909017464843)  # replace 'your-guild-id' with your server id
        channel = discord.utils.get(guild.channels, id=1111031641620619385)  # replace 'your-channel-id' with your photo channel id
        await channel.send(file=picture)

        # Post log
        log_channel = discord.utils.get(guild.channels, id=1112200491422711890)  # replace 'LOG_CHANNEL_ID' with the actual log channel id
        log_message = await create_log_message(latest_file)
        await log_channel.send(log_message)

class ImageHandler(FileSystemEventHandler):
    def __init__(self, queue):
        self.queue = queue

    def on_created(self, event):
        print(f"event type: {event.event_type}  path : {event.src_path}")
        self.queue.put_nowait(event)


async def create_log_message(image_file):
    log_data = load_log_file()  # Load the log data from the JSON file

    # Find the log entry for the current image file
    log_entry = None
    for entry in log_data:
        if entry["image_filename"] == os.path.basename(image_file):
            log_entry = entry
            break

    # Create the log message
    if log_entry:
        message = f"```json\n"
        message += f"Image: {log_entry['image_filename']}\n"
        message += f"Seed: {log_entry['seed']}\n"
        message += f"Timestamp: {log_entry['timestamp']}\n"
        message += f"Prompt: {log_entry['prompt']}\n"
        message += f"```"
    else:
        message = "Log entry not found for the image file."
    return message

def load_log_file():
    log_file = path + 'log.json'  # Path to the log file
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            try:
                log_data = json.load(f)
                return log_data
            except json.JSONDecodeError:
                print("Failed to load log file. Invalid JSON format.")
    else:
        print("Log file not found.")
    return []

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    path_to_watch = path  # your directory here
    queue = asyncio.Queue()
    event_handler = ImageHandler(queue)
    observer = Observer()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()

    while True:
        event = await queue.get()
        if event.src_path.endswith(('.png', '.jpg', '.jpeg')):
            await post_latest_image()

@client.event
async def on_message(message):
    if message.channel.id == CHANNEL_ID:
    # don't respond to ourselves
        if message.author == client.user:
            return

        if message.content.startswith('-!'):
            await handle_command(message) 

async def handle_command(message):
    prompts_file = path + 'prompts.txt'
    # command_parts = message.content.split()
    command_parts = shlex.split(message.content)
    command_name = command_parts[0][2:]  # Remove '-!' from the start
    command_args = command_parts[1:]

    # Help command-----------------------
    if command_name == 'help':  
        await message.channel.send(f'```Available commands are: \n\t-!sp - set image parameters\n\t-!parameters / -!param - list current image parameters\n\t-!reset - reset image parameters to factory default\n\t-!add - add a new prompt to the list\n\t-!undo - undo the deletion of the last added prompt\n\t-!delete - delete the n-th prompt in the list\n\t-!prompts / -!list - lists all prompts in the list```')
   
    # Add prompt command-----------------
    elif command_name == 'add':  
        if len(command_args) < 1:
            await message.channel.send(f'```-!add command must be followed by a prompt to add to the prompt list. \n\n\te.g.: \n\t\t-!add "dummy text 1"```')

        elif command_args[0] == 'help':
            await message.channel.send(f'```Add a prompt to the prompt list. \n\n\te.g.: \n\t\t-!add "dummy text 1"```')
            
        elif not command_args:
            await message.channel.send(f'```-!add command must be followed by a prompt to add to the prompt list. \n\n\te.g.: \n\t\t-!add "dummy text 1"```')
        
        else:
            prompt_to_add = ' '.join(command_args)  # Join all parts to a single string
            with open(prompts_file, 'a') as f:
                f.write(prompt_to_add + '\n')
            await message.channel.send(f'```Added "{prompt_to_add}" to prompts.txt```')

    # Undo prompt command--------------
    elif command_name == 'undo':  
        with open(prompts_file, 'r') as f:
            lines = f.readlines()
        if len(lines) > 0:  # make sure there's at least one line to delete
            deleted_line = lines[-1]  # store the last line
            del lines[-1]  # delete the last line
            with open(prompts_file, 'w') as f:
                f.writelines(lines)
            await message.channel.send(f'```Deleted the last added prompt: \n\n\t {deleted_line}```')
        else:
            await message.channel.send(f'```No prompts to delete```')
    
    #Delete specific prompt command-----
    elif command_name == 'delete':
        if len(command_args) < 1:
            await message.channel.send(f'```-!delete command must be followed by a line number to delete from the prompt list. \n\n\te.g.: \n\t\t-!delete 2```')
        elif not command_args[0].isdigit():
            await message.channel.send(f'```-!delete command must be followed by a numeric line number. \n\n\te.g.: \n\t\t-!delete 2```')
        else:
            line_number = int(command_args[0])
            await delete_line_from_file(prompts_file, line_number, message)

    # List prompts command--------------
    if command_name == 'prompts' or command_name == 'list':
        with open(prompts_file, 'r') as f:
            lines = f.readlines()
        if len(lines) > 0:  # make sure there's at least one line to list
            prompt_list = "\n".join(f'\tPrompt {i+1}: {line.strip()}\n' for i, line in enumerate(lines))
            await message.channel.send(f'```Here are the current prompts:\n\n{prompt_list}```')
        else:
            await message.channel.send(f'```There are currently no prompts in the list```')
    
    # Set parameter command--------------
    elif command_name == 'sp':
        if len(command_args) < 1:
            await message.channel.send(f'```-!sp must be followed by: param_name param_value \n\n\te.g.: \n\t\t-!sp seed 40000000, or help```')
        
        elif command_args[0] == 'help':
            if len(command_args) > 1 and command_args[1] in PARAMS_DESC:
                param_name = command_args[1]
                param_desc = PARAMS_DESC[param_name]
                await message.channel.send(f'```{param_name}: \n {param_desc}```') 
            else:
                await message.channel.send(f'```Available parameters are: \n\t' + '\n\t'.join(AVAILABLE_PARAMS) + '```')
        
        elif len(command_args) != 2:
            await message.channel.send(f'```-!sp must be followed by: param_name param_value \n\n\te.g.: \n\t\t-!sp seed 4000000, or help```')
        
        else:
            param_name = command_args[0]
            param_value = command_args[1]

            write_param_to_file(param_name, param_value)

            await message.channel.send(f'```Set {param_name} to {param_value}```')

    # Print parameters file command--------------        
    elif command_name == 'parameters' or command_name == 'param':  
        parameters_file = path + 'parameters.txt'
        with open(parameters_file, 'r') as f:
            lines = f.readlines()
        if len(lines) > 0:  # make sure there's at least one line to list
            param_list = "\n".join(f'\t{line.strip()}' for line in lines)
            await message.channel.send(f'```Current parameters:\n\n{param_list}```')
        else:
            await message.channel.send(f'```There are currently no parameters set```')

    # Reset parameter command-----------
    elif command_name == 'reset':
        for param_name, default_value in default_parameters.items():
            write_param_to_file(param_name, default_value)
        param_list = '\n'.join(f'{key}: {value}' for key, value in default_parameters.items())
        await message.channel.send(f'```All parameters reset to default values:\n\n{param_list}```')


def write_param_to_file(param_name, param_value):
    parameters_file = path + 'parameters.txt'

    # Read the existing lines
    with open(parameters_file, 'r') as file:
        lines = file.readlines()

    # Check each line for the parameter to update
    for i, line in enumerate(lines):
        if line.startswith(f'{param_name}='):
            # This is the line to update, replace it
            lines[i] = f'{param_name}={param_value}\n'

    # Write the lines back to the file
    with open(parameters_file, 'w') as file:
        file.writelines(lines)

#Delete prompt from file-------------------
async def delete_line_from_file(filename, line_number, message):
    # Read all the lines from the file
    with open(filename, 'r') as file:
        lines = file.readlines()

    # Check if the line to delete is in the range of the lines
    if line_number < 1 or line_number > len(lines):
        await message.channel.send(f'```Invalid prompt number {line_number} for deletion. List has {len(lines)} prompts.```')
        return

    # Store the line to delete
    deleted_line = lines[line_number - 1].strip()

    # Delete the specific line
    del lines[line_number - 1]

    # Write the lines back to the file
    with open(filename, 'w') as file:
        file.writelines(lines)

    await message.channel.send(f'```Deleted prompt {line_number}: "{deleted_line}"```')

















client.run('your-bot-token')  # replace 'your-bot-token' with your bot token
