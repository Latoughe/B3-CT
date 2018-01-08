import redis
import time

time.sleep(5)

r = redis.StrictRedis(host='db', port=6379, db=0)

r.set('test', 'working')

i = r.get('test')
o = i.decode("utf-8")

print(o)


from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
                           title='Home')

@app.route('/add', methods=['POST', 'GET'])
def add():
    if request.method == 'POST':
        r.set(request.form['key'], request.form['value'])

    return 'Successfully added key ' + request.form['key']

@app.route('/get', methods=['POST'])
def get():
    try:
        if request.method == 'POST':
            keyBytes = r.get(request.form['key'])
            key = keyBytes.decode('utf-8')
        return 'You asked about key ' + request.form['key'] + ". Value : " + key
    except:
        return 'Key ' + request.form['key'] + " does not exist."


if __name__ == '__main__':
    app.run(host='0.0.0.0')
