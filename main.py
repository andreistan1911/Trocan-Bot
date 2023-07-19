import requests
import json
import time
import random
import os
from datetime import datetime, timedelta
import pytz
import requests.exceptions

prompt_dic = {
    "dummy_1" : "dummy text 1",
    "dummy_2" : "dummy text 2"
}

# Parameters:
N = 10      # Nr photos to generate
size = 512  # Size of photo (square ratio)
prompt_name = "dummy_1" # Choose one from the list above
iterations = 2          # low: 1 or 2 for size=512, high: around 50-100 for size=1024
path = r'/home/opc/trocan'      # where the photos will be saved
prompt = prompt_dic[prompt_name] 
#prompt = "whatever you want"
cooldown_3_min = True
######################

timezone = pytz.timezone('Europe/Bucharest')


if not path.endswith('/'):
    path += '/'

os.makedirs(path, exist_ok=True)

parameters = path + "parameters.txt"
# Check if the file exists
if not os.path.exists(parameters):
    # If it doesn't exist, create a new file with an empty array
    with open(parameters, 'w') as file:
        file.write('seedrand=0\n')
        file.write('seed=3029190890\n')
        file.write('promptrand=0\n')
        file.write('default=dummy text 1\n')
        file.write('verde=dummy text 2\n')

def read_variables_from_file(parameters):
    variables = {}
    with open(parameters, 'r') as file:
        for line in file:
            # split the line into name and value
            name, value = line.strip().split('=')
            # store in the dictionary
            variables[name.strip()] = value.strip()
    return variables

filename = path + "last_run_time.json"

file_bot = os.path.join(path, 'log.json')
# Check if the file exists
if not os.path.isfile(file_bot):
     # If it doesn't exist, create a new file with an empty array
    with open(file_bot, 'w') as fileb:
        json.dump([], fileb)

file_prompt = os.path.join(path, 'prompts.txt')
# Check if the file exists
if not os.path.isfile(file_prompt):
     # If it doesn't exist, create a new file with an empty array
    with open(file_prompt, 'w') as filep:
        json.dump({}, filep)

def save_last_run_time(time):
    with open(filename, 'w') as f:
        # save the time as a string
        json.dump(time.strftime("%Y-%m-%d %H:%M:%S"), f)

def get_last_run_time():
    with open(filename, 'r') as f:
        # load the time from the string
        return datetime.strptime(json.load(f), "%Y-%m-%d %H:%M:%S")

#def is_next_day():
#    if os.path.exists(filename):
#        last_run_time = get_last_run_time()
#        next_day_plus_four_hours = datetime(last_run_time.year, last_run_time.month, last_run_time.day) + timedelta(days=1, hours=4)
#        if datetime.now() > next_day_plus_four_hours:
#            # It's past 04:00 on the day after the last run
#            save_last_run_time(datetime.now())
#            return True
#        else:
#            return False
#    else:
#        # this is the first run, so save the time and return False
#        save_last_run_time(datetime.now())
#        return False

def check_empty_file(filename):
    with open(filename, 'r') as file:
        contents = file.read().strip()
        return contents == "{}"


def main() :

    #VARIABLES BLOCK----------------------------------------------------------
    variables = read_variables_from_file(parameters)

    seedrand = variables.get('seedrand') #0 = rand, 1 = static
    seedrand = int(seedrand)
    if seedrand == 1:
        seed = variables.get('seed')
    else:
        seed = str(random.randint(3029190890, 6029190890))
    promptrand = variables.get('promptrand') #0 = default, 1 = femeia in verde, 2 = random
    promptrand = int(promptrand)
    default = variables.get('default')
    verde = variables.get('verde')
    if promptrand == 0:
        prompt = default
    else: 
        if promptrand == 1:
            prompt = verde
        else:
            if promptrand == 2:
                is_empty = check_empty_file(file_prompt)
                if is_empty:
                    prompt = default 
                else :
                    with open(file_prompt, 'r') as fileprompt:
                        lines = fileprompt.readlines()
                        prompt = random.choice(lines).strip()
                        prompt = f'"{prompt}"'
            else:
                prompt = default

    #print(' Seedrand = ', seedrand, '\n', 'Seed = ' + seed + '\n', 'Promptrand = ', promptrand, '\n', 'Default = ' + default + '\n', 'Verde = ' + verde + '\n')
    #VARIABLES BLOCK----------------------------------------------------------
     
    log_data = []

#    if is_next_day() == True :
#        cooldown_3_min = False
#    else :
#        cooldown_3_min = True
    
#    if cooldown_3_min :
#        print("-------------Limita de membru free a fost depasita azi!")
#    else :
#        print("-------------15 poze rapide urmeaza!")
    
    while True:  # start a loop that will only break when all images have been successfully requested
        try:
            for i in range(N):
                
                #VARIABLES BLOCK----------------------------------------------------------
                variables = read_variables_from_file(parameters)

                seedrand = variables.get('seedrand') #0 = rand, 1 = static
                seedrand = int(seedrand)
                if seedrand == 1:
                    seed = variables.get('seed')
                else:
                    seed = str(random.randint(3029190890, 6029190890))
                promptrand = variables.get('promptrand') #0 = default, 1 = femeia in verde, 2 = random
                promptrand = int(promptrand)
                default = variables.get('default')
                verde = variables.get('verde')
                if promptrand == 0:
                    prompt = default
                else: 
                    if promptrand == 1:
                        prompt = verde
                    else:
                        if promptrand == 2:
                            is_empty = check_empty_file(file_prompt)
                            if is_empty:
                                prompt = default 
                            else :
                                with open(file_prompt, 'r') as fileprompt:
                                    lines = fileprompt.readlines()
                                    prompt = random.choice(lines).strip()
                                    prompt = f'"{prompt}"'
                        else:
                            prompt = default
                print(' Seedrand = ', seedrand, '\n', 'Seed = ' + seed + '\n', 'Promptrand = ', promptrand, '\n', 'Default = ' + default + '\n', 'Verde = ' + verde + '\n')
                #VARIABLES BLOCK---------------------------------------------------------

#                if cooldown_3_min == False and i >= 15 :
#                    cooldown_3_min = True
                url1 = 'https://editor.imagelabs.net/txt2img'
                
                time_now = datetime.now(timezone)
                print(time_now.strftime("%H:%M:%S") + " - Creating with prompt: " + prompt + ".")
                    
                payload1 = {
                    "prompt": prompt,
                    "seed": seed,
                    "subseed": str(704221346),
                    "subseed_strength": 0.1,
                    "cfg_scale": 2,
                    "width": size,
                    "height": size,
                    "tiling": False,
                    "negative_prompt": "None",
                    "restore_faces": True,
                    "model": "general",
                    "site": "PornLabs.net",
                    "pose": "None"
                }

                response1 = requests.post(url1, json=payload1)
                task_id = None
                
                if response1.status_code == 200:
                    response_json1 = response1.json()
                    if 'task_id' in response_json1:
                        task_id = response_json1['task_id']
                    else:
                        print("'task_id' not in response")
                else:
                    print('Request failed with status code', response1.status_code)
                    print(response1.json())

                if task_id is None:
                    continue

                print(time_now.strftime("%H:%M:%S") + " - Waiting for txt2img request...")
                time.sleep(random.randint(1, 5))
                print(time_now.strftime("%H:%M:%S") + " - Finished txt2img request.")

                url2 = 'https://editor.imagelabs.net/progress'  # replace with your second URL
                payload2 = {
                    "task_id": task_id  # use task_id retrieved from first request
                }

                print(time_now.strftime("%H:%M:%S") + " - Waiting for the first progress...")
                requests.post(url2, json=payload2)
                time.sleep(random.randint(35, 49))
                print(time_now.strftime("%H:%M:%S") + " - Finished the first progress.")

                for i in range(iterations):
                    print(time_now.strftime("%H:%M:%S") + f" - Waiting for progress nr {i + 2}...")
                    requests.post(url2, json=payload2)
                    time.sleep(random.randint(7, 10))
                    print(time_now.strftime("%H:%M:%S") + f" - Finished progress nr {i + 2}.")
                
                response2 = requests.post(url2, json=payload2)

                if response2.status_code == 200:
                    response_json2 = response2.json()

                    image_url = response_json2.get('current_image_url') or response_json2.get('final_image_url')

                    if image_url:
                        # Get image data
                        response3 = requests.get(image_url)
                        # Ensure the request was successful
                        if response3.status_code == 200:
                            # Save image to a file
                            image_dir = path  # specify your folder path here
                            counter = 1
                            while True:
                                image_path = os.path.join(image_dir, f'image{counter}.png')
                                if not os.path.exists(image_path):
                                    break
                                counter += 1

                            with open(image_path, 'wb') as f:
                                f.write(response3.content)
                            print(f"Image saved to {image_path}")

                        # Here we can create a dictionary with the desired fields and append it to the log_data list
                            log_entry = {
                                'seed': seed,
                                'image_filename': f'image{counter}.png',
                                'timestamp': time_now.strftime("%Y-%m-%d %H:%M:%S"),
                                'prompt': prompt
                            }
                            log_data.append(log_entry)

                        else:
                            print('Failed to fetch image data')
                        
                        # Read the existing data from the file
                        with open(file_bot, 'r') as file:
                            existing_data = json.load(file)

                        # Append new log entry to existing data
                        existing_data.extend(log_data)

                        # Write the updated data back to the file
                        with open(file_bot, 'w') as file:
                            json.dump(existing_data, file, indent=4)
                else:
                    print("Neither 'current_image_url' nor 'final_image_url' found in response")
 
                if (cooldown_3_min):
                    print(datetime.now().strftime("%H:%M:%S") + " - Waiting 3 minutes...")
                    time.sleep(random.randint(180, 190))
                    print(datetime.now().strftime("%H:%M:%S") + " - Finished 3 minutes.")
            break

        except requests.exceptions.ConnectionError as err:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + f" - Connection error occurred: {err}. Retrying after 1 hour.")
            time.sleep(60 * 60)  # wait for an hour

if __name__ == "__main__":
    main()
