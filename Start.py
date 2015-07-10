__author__ = 'Benco'


import webbrowser
import os

if __name__ == '__main__':
    path = os.path.join(os.getcwd(),'Main.py')
    os.popen('python %s' % path)
    webbrowser.open('http://127.0.0.1:8888/')