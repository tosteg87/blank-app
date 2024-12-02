import time
from threading import Thread
import os
from app import app

#port=int(os.getenv('PORT'), 10000)

def start():
    #app.run(host='0.0.0.0', port=port, debug=True)
    app.run()

if __name__ == '__main__':
    t = Thread(target=start)
    t.start()
    #app.run(host='0.0.0.0', port=port)
