from flask import Flask, render_template, request
import json
from openai import OpenAI
import os.path
from dotenv import load_dotenv
import logging
import inspect
import os
from datetime import datetime

load_dotenv('env_vars.env')
app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
drinks_menu_json_url = "static/DrinksMenu.json"

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler()])

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    global currentState
    currentState = "CHAT"
    global conversationMemory
    conversationMemory = ""
    with app.open_resource(drinks_menu_json_url) as f:
        drinks_menu = json.load(f)["drinks_menu"]
    return render_template('index.html', drinks_menu=drinks_menu)

@app.route('/process_speech', methods=['POST'])
def process_speech():
    global prompts
    global currentState # JAKE - This is the current state/action we are in. For example it could be set to 'CHAT' or 'DRINKS'
    global conversationMemory
    capture_trace("Current action: " + currentState)

    prompts = get_prompts_from_file('prompts.txt')
    customer_speech = request.form['customer_speech']
    # JAKE - We should definitely refactor the following 'action tree' / state machine to something more elegant than a beefy If statement, but it's working as a proof of concept.
    if(currentState == "CHAT"): # JAKE - The first state check is if we are in CHAT mode then we go to the chat_or_action LLM.
                                # this LLM will either respond with regular conversation, OR it will change the currentState to the action we are now focussed on
                                # for example, if the customer is talking about beer, it will move us into the "DRINKS" state
        reply = chat_or_action_LLM(customer_speech)
    if(currentState == "DRINKS"):
        order_valid, order_guidance = verify_drinks_order_LLM(conversationMemory + customer_speech) # This here will be the same customer_speech from above that was ignored by the top-level model
        if order_valid:
            order_json = generate_drinks_order_json_LLM(order_guidance)
            capture_trace("Order was valid:" + order_json)
            currentState = "CHAT"
            conversationMemory = conversationMemory + ".\n" + customer_speech + ".\nOrder placed successfully" # JAKE - can see here where the conversation memory is updated - however, in this 'order successful' state, we may actually want to perform the conversation summarise step
            return "Order placed successfully : " + order_json
        else:
            capture_trace("Order was invalid")
            conversationMemory = conversationMemory + ".\n" + customer_speech + ".\n" + order_guidance + ".\n" # JAKE - can see here where the conversation memory is updated
            return order_guidance
    if(currentState == "LIGHTS"): # JAKE - Can see here how this model could be expanded for light operation or something
        capture_trace("NOT IMPLEMENTED: My apologies, we are working hard behind the scenes to personalise you lighting experience")
        currentState = "CHAT" # Return to chat state after ordering
    if(currentState == "FOOD"): # JAKE - Can see here how this model could be expanded for light operation or something
        capture_trace("NOT IMPLEMENTED: My apologies, we have no food on offer today")
        currentState = "CHAT" # Return to chat state after ordering
    return reply

def chat_or_action_LLM(customer_speech):
    global currentState
    prompt = prompts["CHAT"]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt },
            {"role": "user", "content": customer_speech}
        ]
    )
    reply = response.choices[0].message.content
    capture_trace(reply)
    actionNeeded = (reply[0] == '#') # JAKE - I would advice reading the prompts in prompts.txt to see why I'm doing this
                                    # Essentially, hashes are used to mark actions
                                    # No hash, no action
    capture_trace("ACTION NEEDED: " + str(actionNeeded))
    if(actionNeeded):
        currentState = whichAction(reply)
        return reply
    else:
        currentState = "CHAT" # JAKE - No state movement, we can continue to just converse
        return reply

def verify_drinks_order_LLM(order_input): # JAKE - All function that are directly dealing with LLMS now end in 'LLM' for clarity
    capture_trace("INPUT IS:" + order_input)
    drinks_menu_lines = read_file_as_string(drinks_menu_json_url)
    prompt = prompts["VALIDATE"] + "\n" + drinks_menu_lines # JAKE - you can reference this prompts[] dictionary in each of the LLM functions to see which prompt in prompts.txt they are using
                                                            # for example, this function uses the VALIDATE prompt
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt },
            {"role": "user", "content": order_input}
        ]
    )
    capture_trace(response.choices[0].message.content)
    order_valid, order_guidance = split_at_first_colon(response.choices[0].message.content)
    order_valid = (order_valid == 'VALID') # conversion to bool
    return order_valid, order_guidance

def generate_drinks_order_json_LLM(user_order):
    drinks_menu_lines = read_file_as_string(drinks_menu_json_url)
    prompt = prompts["JSON"] + "\n" + drinks_menu_lines
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_order}
        ]
    )
    return response.choices[0].message.content

def whichAction(string):
    string = string.strip()
    action = string.strip('#')
    return action

def get_prompts_from_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    doubleNewlineDivisions = content.split('\n\n')
    prompts = {}
    for prompt in doubleNewlineDivisions:
        promptKey = prompt.split('--')[1] # Get prompt dict key (prompt title)
        prompts[promptKey] = prompt.split('--')[2]
    return prompts

def read_file_as_string(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"

def split_at_first_colon(input_string):
    before_colon = ''
    after_colon = ''
    colon_found = False
    for char in input_string:
        if char == ':':
            colon_found = True
            continue
        if colon_found:
            after_colon += char
        else:
            before_colon += char
    return before_colon, after_colon

def capture_trace(trace, filename='captured_trace/captured_trace.log'):
    # get function caller for debugging help
    current_frame = inspect.currentframe()
    caller_frame = current_frame.f_back
    caller_name = caller_frame.f_code.co_name
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not os.path.exists('captured_trace'):
        os.makedirs('captured_trace')

    with open(filename, 'a') as log_file:
        log_file.write(current_timestamp + f" {caller_name}:\n" + trace + "\n")


if __name__ == '__main__':
    app.run(debug=True)
