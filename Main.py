__author__ = 'Benco'

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.auth
import tornado.options
import os
import pymongo
import hashlib
import datetime
import json
import logging

from tornado.web import authenticated
from tornado.options import define, options

define("port", default=8888, help="Run On The Given Port", type=int)

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.db = self.settings['db']
        self.user = self.db.get_collection('user')
        self.notebook = self.db.get_collection('notebook')
        self.note = self.db.get_collection('note')

    def get_current_user(self):
        return self.get_secure_cookie('username')

class MainHandler(BaseHandler):
    def get(self):
        self.write("Fuck WebEngine")

class IndexHandler(BaseHandler):
    def get(self):
        self.render("index.html")

class LoginHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.render('login.html')
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        print(username, password)
        doc = self.user.find_one({'username':username})
        print(doc)
        if doc == None:
            self.redirect('/login.html')
        real_password = doc['password']
        if password == real_password:
            logging.info("Login Successfully")
            self.set_secure_cookie('username',username)
            self.write(json.dumps({'ok':True}))
            self.redirect('/')
        else :
            logging.info("Successful Failed")
            self.redirect('/login.html')


class RegisterHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.render('register.html')
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        print(username, password)
        doc = self.user.find_one({'username':username})
        print(doc)
        if doc == None:
            self.user.insert({'username':username,'password':password})
            self.write(json.dumps({'ok':True}))
            self.redirect('/')
        else :
            self.write(json.dumps({"ok":False}))
            self.redirect('/register.html')

class NoteBookHandler(BaseHandler):
        @authenticated
        def get(self):
            self.write("Mind Me Fucking?!")

class CreateNoteBookHandler(NoteBookHandler):


    def post(self):
        msg = json.loads(self.request.body.decode())
        self.notebook.insert(msg)
        self.write(json.dumps({"ok":True}))
        logging.info("Create Successfully")

class UpdateNoteBookHandler(NoteBookHandler):

    def post(self, notebookid):
        msg = json.loads(self.request.body.decode())
        doc = self.notebook.find_one_and_delete({'notebookid':notebookid})
        doc['notebook_name'] = msg['notebook_name']
        doc['notebook_description'] = msg['notebook_description']
        doc['create_date'] = msg['create_date']
        doc['change_date'] = msg['change_date']
        self.notebook.insert(msg)
        logging.info("Update Successfully")

class DeleteNoteBookHandler(NoteBookHandler):

    def post(self, notebookid):
        delresult= self.notebook.delete_one({'notebookid':notebookid})
        if delresult == None:
            logging.info("Delete Failed")
        else :
            logging.info("Delete %s Successfully" % delresult)

class CheckNoteBookHandler(BaseHandler):
    pass

class NoteHandler(BaseHandler):
        @authenticated
        def get(self):
            self.write("Mind Me Fucking?!")

class CreateNoteHandler(NoteHandler):


    def post(self):
        msg = json.loads(self.request.body.decode())
        self.note.insert(msg)
        self.write(json.dumps({"ok":True}))
        logging.info("Create Successfully")

class UpdateNoteHandler(NoteHandler):

    def post(self, noteid):
        msg = json.loads(self.request.body.decode())
        doc = self.note.find_one_and_delete({'noteid':noteid})
        doc['note_name'] = msg['note_name']
        doc['note_description'] = msg['note_description']
        doc['create_date'] = msg['create_date']
        doc['change_date'] = msg['change_date']
        self.note.insert(msg)
        logging.info("Update Successfully")

class DeleteNoteHandler(NoteHandler):

    def post(self, noteid):
        delresult= self.note.delete_one({'noteid':noteid})
        if delresult == None:
            logging.info("Delete Failed")
        else :
            logging.info("Delete %s Successfully" % delresult)

class CheckNoteHandler(BaseHandler):
    pass

class FuckHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.write("fuck u")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),
            (r'/login', LoginHandler),
            (r'/register', RegisterHandler),
            (r'/fuck', FuckHandler),
        ]
        settings = dict(
            static_path = os.path.join(os.path.dirname('__file__'), 'static'),
            template_path = os.path.join(os.path.dirname('__file'), 'template'),
            debug = True,
            cookie_secret = 'fuckthewebengineeringhomework',
            login_url = '/login.html',
            db = pymongo.MongoClient('localhost', 27017).get_database('WebEngineering'),
        )
        tornado.web.Application.__init__(self,handlers,**settings)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    application = Application()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


