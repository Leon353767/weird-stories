from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>TEST: Flask is working!</h1><p>If you see this, the problem is in your templates.</p>"

if __name__ == '__main__':
    app.run(debug=True)