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
def proce6ss_order():
    order_input = request.form['order']
    order_valid, order_guidance = verify_order(order_input)
    if(order_valid):
        order_json = generate_order_json(order_guidance)
        return "Order placed successfully\n"
    else:
        return order_guidance

def read_file_as_string(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"

def verify_order(order_input):
    drinks_menu_lines = read_file_as_string(drinks_menu_json_url)
    print(drinks_menu_lines)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You assist people with their drinks order.\nHere is the drinks menu for the restaurant:{drinks_menu_lines}\nIf the customers order is valid, return the word 'VALID:' (colon included) followed by a simple list of their order.\nIf the customers order is invalid, return the word 'INVALID:' (colon included) followed by an apology and the reason(s) why the order can't be fulfilled based on the drinks menu. Keep in mind, some items may just be spelled incorrectly, so use your best judgement to simply correct the incorrectly spelled items if you can see an item that matches, and then pass it as valid. If no size is specified, assume the largest drink option."},
            {"role": "user", "content": order_input}
        ]
    )
    order_valid, order_guidance = split_at_first_colon(response.choices[0].message.content)
    print(order_valid)
    print(order_guidance)
    order_valid = (order_valid == 'VALID') # conversion to bool
    return order_valid, order_guidance

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

def generate_order_json(user_order):
    drinks_menu_lines = read_file_as_string(drinks_menu_json_url)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": f"You are a helpful assistant that converts a customers drink order to JSON.\nHere is the drinks menu: {drinks_menu_lines}"},
            {"role": "user", "content": user_order}
        ]
    )
    return response.choices[0].message.content

if __name__ == '__main__':
    app.run(debug=True)
