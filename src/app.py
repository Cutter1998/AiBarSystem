from flask import Flask, render_template, request
import json
from openai import OpenAI
import os.path
from dotenv import load_dotenv

load_dotenv('env_vars.env')
app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
drinks_menu_json_url = "static/DrinksMenu.json"

@app.route('/')
def index():
    with app.open_resource(drinks_menu_json_url) as f:
        drinks_menu = json.load(f)["drinks_menu"]
    return render_template('index.html', drinks_menu=drinks_menu)

@app.route('/process_order', methods=['POST'])
def process_order():
    global prompts
    prompts = get_prompts_from_file('prompts.txt')
    order_input = request.form['order']
    order_valid, order_guidance = verify_order(order_input)
    if order_valid:
        order_json = generate_order_json(order_guidance)
        return "Order placed successfully" 
    else:
        return order_guidance

def verify_order(order_input):
    drinks_menu_lines = read_file_as_string(drinks_menu_json_url)
    prompt = prompts["VALIDATE"] + "\n" + drinks_menu_lines
    print(prompt)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt },
            {"role": "user", "content": order_input}
        ]
    )
    print(response.choices[0].message.content)
    order_valid, order_guidance = split_at_first_colon(response.choices[0].message.content)
    print(order_valid)
    print(order_guidance)
    order_valid = (order_valid == 'VALID') # conversion to bool
    return order_valid, order_guidance

def generate_order_json(user_order):
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

if __name__ == '__main__':
    app.run(debug=True)
