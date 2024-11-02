from flask import Flask
from flask import render_template
from flask import request

app = Flask(__name__)

@app.route("/")
def hello_world():

    return "<p>Hello, World!</p>"
if __name__ == 'main':
  app.run(debug=True)

@app.route('/about')
def about():
  return 'This is the about page'

@app.route('/user/<username>')
def show_user_profile(username):
  return f'User {username}'

@app.route('/hello/<name>')
def hello(name):
  return render_template('hello.html', name=name)

@app.route('/greet/<name>')
def greet(name):
  return f'Hello, {name}!'

@app.route('/submit', methods=['POST'])
def submit():
  name = request.form['name']
  return f'Hello, {name}'
