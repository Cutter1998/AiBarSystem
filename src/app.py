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
    global current_state
    current_state = "CHAT"
    global conversation_memory
    conversation_memory = ""
    with app.open_resource(drinks_menu_json_url) as f:
        drinks_menu = json.load(f)["drinks_menu"]
    return render_template('index.html', drinks_menu=drinks_menu)
    
@app.route('/process_speech', methods=['POST'])
def process_speech():
    global prompts
    global current_state
    global conversation_memory
    prompts = get_prompts_from_file('prompts.txt')
    customer_speech = request.form['customer_speech']
    reply = handle_customer_speech(current_state, customer_speech)
    return reply    

def handle_customer_speech(current_state, customer_speech):
    global conversation_memory
    capture_trace("Current state is" + current_state)

    if(current_state == "CHAT"): # if we are at the top level, we need to either respond with normal conversartion, or move to an action state if customer_speech requires action
        reply = chat_or_action_LLM(customer_speech, conversation_memory)
        actionNeeded = (reply[0] == '#') # determine if action is needed
        if(actionNeeded):
            current_state = which_action(reply)
        else:
            current_state = "CHAT" # if no action required, we can remain in CHAT state

    if(current_state == "DRINKS"):
        order_valid, order_guidance = verify_drinks_order_LLM(conversation_memory + customer_speech)
        if order_valid:
            order_json = generate_drinks_order_json_LLM(order_guidance)
            capture_trace("Order valid")
            capture_trace(order_json)
            current_state = "CHAT" # move back to chat, drinks order placed successfully
            reply = "Order placed successfully"
        else:
            capture_trace("Order invalid")
            current_state = "DRINKS" # remain in DRINKS state because the order was invalid
            reply = order_guidance
        
    if(current_state == "LIGHTS"):
        capture_trace("NOT IMPLEMENTED")

    update_conversation_memory(customer_speech, reply)
    
    return reply

def update_conversation_memory(customer_speech, reply):
    global conversation_memory
    conversation_memory = conversation_memory + "\n" + "Customer: " + customer_speech + "\nYou: " + reply

def chat_or_action_LLM(customer_speech, conversation_history):
    global current_state
    prompt = prompts["CHAT"] + conversation_history
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt },
            {"role": "user", "content": customer_speech}
        ]
    )
    reply = response.choices[0].message.content
    return reply

def verify_drinks_order_LLM(order_input):
    drinks_menu_lines = read_file_as_string(drinks_menu_json_url)
    prompt = prompts["VALIDATE"] + "\n" + drinks_menu_lines
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt },
            {"role": "user", "content": order_input}
        ]
    )
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

def which_action(string):
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