from flask import Flask, render_template, request
from openai import OpenAI
import requests
import os.path
from dotenv import load_dotenv

load_dotenv('env_vars.env')
app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_order_summary', methods=['POST'])
def get_order_summary():
    order_field = {}
    order_field["order"] = request.form['order']
    generate_order(order_field["order"])
    return "response"

def generate_order(user_order):
    print(user_order)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes customers drink orders ready for a automated bartender in JSON."},
            {"role": "user", "content": user_order}
        ]
    )
    print(response.choices[0].message.content)

if __name__ == '__main__':
    app.run(debug=True)