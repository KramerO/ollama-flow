#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)

@app.route('/discovery')
def get_discovery():
    return {"message": "Discovery service"}

if __name__ == "__main__":
    app.run(debug=True)
