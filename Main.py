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

    def get_current_user(self):
        return self.get_secure_cookie('username')

class IndexHandler(BaseHandler):
    def get(self):
        boolean = True
        username = None
        date = None
        userid = None
        name = self.get_current_user()
        doc = self.note.find({},{'_id':0}).sort('visit',pymongo.DESCENDING)
        show_note = []
        for _ in doc:
            val = self.note.find_one({'noteid':str(int(_['noteid']))},{'_id':0})
            if val and len(show_note) < 6:
                show_note.append(val)
        if name :
            boolean = False
            username = name.decode()
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

#登陆
class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        doc = self.user.find_one({'username':username})
        if doc != None:
            real_password = doc['password']
            if password == real_password:
                self.set_secure_cookie('username',username, expires_days=None)

#注册
class RegisterHandler(BaseHandler):
    def get(self):
        self.render('register.html')
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        doc = self.user.find_one({'username':username})
        count = self.user.count() + 1
        if doc == None:
            self.user.insert({
                'username' : username,
                'password' : password,
                'userid' : str(count),
                'user_description' : 'XDU',
                'register_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            })

# 查看笔记本中的笔记列表 /notebook/notebook_name
class ReadNoteBookHandler(BaseHandler):
    @authenticated
    def get(self,notebook_name):
        username = self.get_current_user().decode()
        show_note = self.note.find({'username':username,'notebook_name':notebook_name})
        # notebookid = self.notebook.find_one({'username':username})['notebookid']
        # doc = self.note.find({'notebookid':notebookid,'username':username})
        # notebook_name = 'Default'
        # show_note = []
        # for _ in doc:
        #     show_note.append(_)
        #     if notebook_name == 'Default':
        #         notebook_name = _['notebook_name']
        self.render(
            'notebook.html',
            show_note = show_note,
            username = username,
            notebook_name = notebook_name,
        )

# 查看笔记 /note/noteid
class ReadNoteHandler(BaseHandler):
    def get(self,noteid):
        username = self.get_current_user().decode()
        userid = self.user.find_one({'username':username})['userid']
        note = self.note.find_one_and_delete({'noteid':noteid},{'_id':0})
        note['visit'] += 1
        self.note.insert(note)
        self.render(
            'note.html',
            note = note,
            userid = userid
        )

#创建笔记 /note/create/notebook_name
class CreateNoteHandler(BaseHandler):
    @authenticated
    def get(self, notebook_name):
        username = self.get_current_user().decode()
        notebookid = self.notebook.find_one({'username':username,'notebook_name':notebook_name})
        # notebook= self.notebook.find_one({'username':username})
        # notebook_name = notebook.get('notebook_name','Default') if notebook else 'Default'
        # notebookid = notebook['notebookid']
        self.render(
            'note_edit.html',
            username = username,
            notebook_name = notebook_name,
            notebookid = notebookid,
        )

    def post(self, notebook_name):
        title = self.get_argument('title')
        content = self.get_argument('content')
        notebookid = self.get_argument('notebookid')
        notebook = self.notebook.find_one({'notebookid':notebookid})
        username = self.get_current_user().decode()
        notebook_name = notebook_name
        count = self.note.count() + 1
        judge = self.note.find_one({'username':username,'note_title':title,'notebook_name':notebook_name})
        if judge == None:
            doc = {
                'note_title' : title,
                'note_content' : content,
                'notebookid' : notebookid,
                'noteid' : str(count),
                'notebook_name' : notebook_name,
                'username' : self.get_current_user().decode(),
                'create_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
                'change_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
                'visit' : 1,
            }
            self.note.insert(doc)
            self.write(json.dumps({'ok' : True}))

# 查看笔记本集合 /notebook_list/userid
class CreateNoteBookHandler(BaseHandler):
    @authenticated
    def get(self, userid):
        notebooks = self.notebook.find({'userid':userid})
        username = self.user.find_one({'userid':userid})['username']
        self.render(
            'notebook_list.html',
            username = username,
            notebooks = notebooks,
            userid = userid,
        )

#创建笔记本 /notebook/create/username
class FuckNoteBookHandler(BaseHandler):
    @authenticated
    def post(self, username):
        notebook_name = self.get_argument('notebook_name')
        notebook_description = self.get_argument('notebook_description')
        count = self.notebook.count() + 1
        judge = self.notebook.find_one({'username':username,'notebookname':notebook_name})
        userid = self.user.find_one({'username':username})['userid']
        # print("CreateNoteBook : %d %s %s",count,notebook_name,notebook_description)
        if judge == None:
            doc = {
                'notebookid' : str(count),
                'userid':userid,
                'notebook_name' : notebook_name,
                'notebook_description' : notebook_description,
                'username' : self.get_current_user().decode(),
                'create_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
                'change_date' : datetime.now().strftime('%Y-%m-%d %I:%M:%S %p'),
            }
            self.notebook.insert(doc)
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
            (r'/note/create/([0-9a-zA-Z]+)', CreateNoteHandler),
            (r'/notebook_list/([0-9a-zA-Z]+)', CreateNoteBookHandler),
            (r'/notebook/create/([0-9a-zA-Z]+)', FuckNoteBookHandler),
            (r'/notebook/([0-9a-zA-Z]+)', ReadNoteBookHandler),
            (r'/logout', LogoutHandler),
        ]
        settings = dict(
            static_path = os.path.join(os.path.dirname('__file__'), 'static'),
            template_path = os.path.join(os.path.dirname('__file__'), 'template'),
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