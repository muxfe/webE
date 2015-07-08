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
from datetime import *

define("port", default=8888, help="Run On The Given Port", type=int)

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.db = self.settings['db']
        self.user = self.db.get_collection('user')
        self.notebook = self.db.get_collection('notebook')
        self.note = self.db.get_collection('note')
        self.notelist = self.db.get_collection('notelist')

    def get_current_user(self):
        return self.get_secure_cookie('username')

class IndexHandler(BaseHandler):
    def get(self):
        boolean = True
        username = None
        date = None
        name = self.get_current_user()
        doc = self.notelist.find({'private':False},{'_id':0}).sort('visit',pymongo.DESCENDING)
        show_note = []
        for _ in doc:
            show_note.append(self.note.find_one({'noteid':str(int(_['noteid']))},{'_id':0}))
        if name :
            boolean = False
            username = name.decode()
            date = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        #for _ in show_note:
           # print(_)
        self.render(
            'index.html',
            boolean = boolean,
            username = username,
            date = date,
            show_note = show_note,
        )

class LoginHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.render('login.html')
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        #print(username, password)
        doc = self.user.find_one({'username':username})
        #print(doc)
        if doc != None:
            real_password = doc['password']
            if password == real_password:
                logging.info("Login Successfully")
                self.set_secure_cookie('username',username, expires_days=None)
                #self.userinfo['username'] = username
                #self.userinfo['date'] = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
                #self.boolean = False
                #self.redirect('/')
            else :
                logging.info("Successful Failed")
                #self.redirect('/login.html')

class RegisterHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.render('register.html')
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        #print(username, password)
        doc = self.user.find_one({'username':username})
        #print(doc)
        count = self.user.count() + 1
        if doc == None:
            self.user.insert({
                'username' : username,
                'password' : password,
                'userid' : count,
                'user_description' : 'XDU',
                'register_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            })
            #self.redirect('/')

class ReadNoteBookHandler(BaseHandler):
    def get(self):
        self.render('notebook.html')

    def post(self):
        msg = json.loads(self.request.body.decode())
        self.notebook.insert(msg)
        logging.info("Create Successfully")

class ReadNoteHandler(BaseHandler):
    def get(self,noteid):
        notelist = self.notelist.find_one_and_delete({'noteid':noteid})
        notelist['visit'] += 1
        note = self.note.find_one_and_delete({'noteid':noteid},{'_id':0})
        note['visit'] = notelist['visit']
        self.note.insert(note)
        self.notelist.insert(notelist)
        self.render(
            'note.html',
            note = note,
        )

class CreateNoteHandler(BaseHandler):
    @authenticated
    def get(self):
        self.render('note_edit.html')

    def post(self):
        data = self.request.body.decode()
        title = data['title']
        content = data['content']
        notebookid = data['notebookid']
        notebook = self.notebook.find_one({'notebookid':notebookid})
        count = self.note.count() + 1
        doc = {
            'title' : title,
            'content' : content,
            'notebookid' : notebookid,
            'noteid' : count,
            'notebook_name' : notebook['notebookname'],
            'username' : self.get_current_user().decode(),
            'create_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            'change_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
        }
        self.note.insert(doc)
        self.write(json.dumps({'ok' : True}))

class LogoutHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.set_secure_cookie('username','')
        self.redirect('/')

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),
            (r'/login', LoginHandler),
            (r'/register', RegisterHandler),
            (r'/note/([0-9]+)', ReadNoteHandler),
            (r'/note/create', CreateNoteHandler),
            #(r'/note/update/(/d+)', UpdateNoteHandler),
            #(r'/note/delete/(/d+)', DeleteNoteHandler),
            (r'/notebook', ReadNoteBookHandler),
            #(r'/notebook/update/(/d+)', UpdateNoteBookHandler),
            #(r'/notebook/delete/(/d+)', DeleteNoteBookHandler),
            (r'/logout', LogoutHandler),
        ]
        settings = dict(
            static_path = os.path.join(os.path.dirname('__file__'), 'static'),
            template_path = os.path.join(os.path.dirname('__file'), 'template'),
            debug = True,
            cookie_secret = 'fuckthewebengineeringhomework',
            login_url = '/login',
            db = pymongo.MongoClient('localhost', 27017).get_database('WebEngineering'),
        )
        tornado.web.Application.__init__(self,handlers,**settings)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    application = Application()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
'''
class NoteBookHandler(BaseHandler):
        @authenticated
        def get(self):
            self.render('notebook.html')
'''

'''
class UpdateNoteBookHandler(BaseHandler):

    def post(self, notebookid):
        msg = json.loads(self.request.body.decode())
        doc = self.notebook.find_one_and_delete({'notebookid':notebookid})
        doc['notebook_name'] = msg['notebook_name']
        doc['notebook_description'] = msg['notebook_description']
        doc['create_date'] = msg['create_date']
        doc['change_date'] = msg['change_date']
        self.notebook.insert(doc)
        logging.info("Update Successfully")

class DeleteNoteBookHandler(BaseHandler):

    def get(self, notebookid):
        delresult = self.notebook.find_one_and_delete({'notebookid':notebookid})
        if delresult == None:
            logging.info("Delete Failed")
        else :
            logging.info("Delete %s Successfully" % str(delresult))
'''
'''
class NoteHandler(BaseHandler):
        @authenticated
        def get(self):
            self.render('note.html')
'''
'''
class UpdateNoteHandler(BaseHandler):

    def post(self, noteid):
        msg = json.loads(self.request.body.decode())
        doc = self.note.find_one_and_delete({'noteid':noteid})
        doc['note_name'] = msg['note_name']
        doc['note_description'] = msg['note_description']
        doc['create_date'] = msg['create_date']
        doc['change_date'] = msg['change_date']
        self.note.insert(msg)
        logging.info("Update Successfully")

class DeleteNoteHandler(BaseHandler):

    def get(self, noteid):
        delresult= self.note.delete_one({'noteid':noteid})
        if delresult == None:
            logging.info("Delete Failed")
        else :
            logging.info("Delete %s Successfully" % delresult)

class ReadNoteHandler(BaseHandler):

    def get(self, noteid):
        pass
'''



