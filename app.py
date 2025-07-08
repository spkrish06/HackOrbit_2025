from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == '1234':
            return redirect(url_for('index'))  
        else:
            return "Invalid credentials. Try again."

    return render_template('login.html') 


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/trades')
def trades():
    table_html = None
    return render_template('trades.html', table=table_html)

if __name__ == '__main__':
    app.run(debug=True)
