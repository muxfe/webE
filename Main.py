__author__ = 'Benco'

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.auth
import tornado.options
import os
import pymongo
import logging
import json

from tornado.escape import json_decode
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

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Access-Control-Max-Age', 1000)
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Content-type', 'application/json')
    def get_current_user(self):
        return self.get_secure_cookie('username')

class IndexHandler(BaseHandler):
    def get(self):
        boolean = True
        username = None
        date = None
        userid = None
        name = self.get_current_user()
        doc = self.notelist.find({'private':False},{'_id':0}).sort('visit',pymongo.DESCENDING).limit(6)
        show_note = []
        for _ in doc:
            val = self.note.find_one({'noteid':str(int(_['noteid']))},{'_id':0})
            if val :
                show_note.append(val)
        if name :
            boolean = False
            username = name.decode('utf-8')
            userid = self.user.find_one({'username':username})['userid']
            date = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')

        self.render(
            'index.html',
            boolean = boolean,
            username = username,
            userid = userid,
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
                'userid' : str(count),
                'user_description' : 'XDU',
                'register_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            })
            #self.redirect('/')

class ReadNoteBookHandler(BaseHandler):
    @authenticated
    def get(self,username):
        notebookid = self.notebook.find_one({'username':username})['notebookid']
        doc = self.note.find({'notebookid':notebookid,'username':username})
        notebook_name = 'Default'
        show_note = []
        for _ in doc:
            show_note.append(_)
            if notebook_name == 'Default':
                notebook_name = _['notebook_name']
        #print(show_note)
        self.render(
            'notebook.html',
            show_note = show_note,
            username = username,
            notebook_name = notebook_name,
        )
    def post(self, userid):
        pass

class ReadNoteHandler(BaseHandler):
    def get(self,noteid):
        notelist = self.notelist.find_one_and_delete({'noteid':noteid})
        notelist['visit'] += 1
        note = self.note.find_one_and_delete({'noteid':noteid},{'_id':0})
        note['visit'] += 1
        self.note.insert(note)
        self.notelist.insert(notelist)
        self.render(
            'note.html',
            note = note,
        )

#创建笔记
class CreateNoteHandler(BaseHandler):
    @authenticated
    def get(self, username):
        notebook= self.notebook.find_one({'username':username})
        notebook_name = notebook.get('notebook_name','Default') if notebook else 'Default'
        notebookid = notebook['notebookid']
        self.render(
            'note_edit.html',
            username = username,
            notebook_name = notebook_name,
            notebookid = notebookid,
        )

    def post(self, username):
        title = self.get_argument('title')
        content = self.get_argument('content')
        notebookid = self.get_argument('notebookid')
        notebook = self.notebook.find_one({'notebookid':notebookid})
        notebook_name = notebook.get('notebook_name','Default') if notebook else 'Default'
        count = self.note.count() + 1
        doc = {
            'note_title' : title,
            'note_content' : content,
            'notebookid' : notebookid,
            'noteid' : str(count),
            'notebook_name' : notebook_name,
            'username' : self.get_current_user().decode('utf-8'),
            'create_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            'change_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            'visit' : 1,
        }
        lists = {
            'username' : self.get_current_user().decode('utf-8'),
            'private' : False,
            'visit' : 1,
            'noteid' : str(count),
            'change_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
        }
        self.note.insert(doc)
        self.notelist.insert(lists)
        self.write(json.dumps({'ok' : True}))

class CreateNoteBookHandler(BaseHandler):
    @authenticated
    def get(self, username):
        notebooks= self.notebook.find({'username':username})
        #notebook_name = notebook.get('notebook_name','Default') if notebook else 'Default'
        self.render(
            'notebook_list.html',
            username = username,
            notebooks = notebooks,
        )

#创建笔记本
class FuckNoteBookHandler(BaseHandler):
    @authenticated
    def post(self, username):
        notebook_name = self.get_argument('notebook_name')
        notebook_description = self.get_argument('notebook_description')
        count = self.notebook.count() + 1
        doc = {
            'notebookid' : str(count),
            'notebook_name' : notebook_name,
            'notebook_description' : notebook_description,
            'username' : self.get_current_user().decode('utf-8'),
            'create_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            'change_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
        }
        self.notebook.insert(doc)
        self.write(json.dumps({'ok' : True}))
        #self.redirect('/notebook_list/%s'%username)
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
            (r'/note/create/([0-9a-zA-Z]+)', CreateNoteHandler),
            (r'/notebook_list/([0-9a-zA-Z]+)', CreateNoteBookHandler),
            (r'/notebook/create/([0-9a-zA-Z]+)', FuckNoteBookHandler),
            #(r'/note/update/(/d+)', UpdateNoteHandler),
            #(r'/note/delete/(/d+)', DeleteNoteHandler),
            (r'/notebook/([0-9a-zA-Z]+)', ReadNoteBookHandler),
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
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
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



