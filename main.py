import os
import jinja2
import webapp2
import string
import hmac
import random
import operator
import time
import json
import re
import hashlib, binascii

from google.appengine.ext import db

from Modules import Post, Users, Comments


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))


"""
class Handler is the main class that Handler jinjas templates,
it ehreit from webapp2
"""


class MainHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
            self.write(self.render_str(template, **kw))

    """ generate an random salt """
    def generate_salt(self):
        return ''.join(random.choice(string.lowercase) for a in xrange(5))

    """ method for password hash """
    def hash_pass(self, password, salt=None):
        if not salt:  # this allows has_pass to be used for verification also
            salt = self.generate_salt()
            # if no salt gived, generate a new salt
        return "%s|%s" % (salt, binascii.hexlify(hashlib.pbkdf2_hmac('sha256',
                                                                     'haribol',
                                                                     password+salt,
                                                                     100000)))

    """ method to check if user is already logged in """
    def check(self):
        cookie_user_id = self.request.cookies.get('user_id')
        cookie_username = self.request.cookies.get('username')
        if cookie_user_id and cookie_username:
            hashed_id = self.hash_id(cookie_user_id.split('|')[0])
            hashed_name = self.hash_id(cookie_username.split('|')[0])
            if cookie_user_id == hashed_id and cookie_username == hashed_name:
                return [cookie_user_id.split('|')[0],
                        cookie_username.split('|')[0]]
            return None
        else:
        	return None

    """ method to hash user id before sending it to cookie """
    def hash_id(self, user_id):
        return '%s|%s' % (str(user_id),
                          hmac.new('haribol', str(user_id)).hexdigest())

    """ method to set a cookie """
    def set_cookie(self, name, value):
        if value:
            value = self.hash_id(value)
            self.response.headers.add_header('Set-Cookie',
                                             '%s=%s; Path=/' % (name, value))
# if no value means cookie should be empty, i.e logout function
        else:
            self.response.headers.add_header('Set-Cookie',
                                             '%s=%s; Path=/' % (name, value))

    """ method to register the user """
    def register(self, name, password):
        pass

    """ method to login user """
    def login(self, name, password):
        self.redirect('/welcome')

    """ method to logout user """
    def logout(self):
        self.set_cookie('user_id', '')
        self.redirect('/login')

    """ method to make user post """
    def post(self, id, post):
        pass

    """ method to check if the user triyng to edit the post
        is the same user who once created it """
    def check_user(self, creator_id):
        ida = creator_id
        oda = self.check()
        if str(ida) == str(oda):
            return True
        return False


"""
main class for path '/'
"""

class MainPage(MainHandler):
    def get(self):
        check = self.check()
        if check:
            if self.request.get('like'):  # RESOLVER ISTO
                post_id = self.request.get('post_id')
                post_key = db.Key.from_path('Post', int(post_id))
                # used to retrieve an key for the entity
                post = db.get(post_key)
                if not self.check_user(post.creator):
                    if check[0] in post.likes:
                        self.redirect('/')
                    else:
                        post.likes.append(check[0])
                        print post.likes			
                        post.put()
                        time.sleep(0.1)
                        self.redirect('/')
                else:
                    self.redirect('/')
            username = check[1]
            posts = Post.all().order('-created')
            comments = Comments.all().order('-created')
            comment_list = []
            for a in posts:
                for b in a.comments:
                    for x in comments:
                        if str(b) == str(x.key().id()):
                            comment_list.append(
                                               {'post': a.key().id(),
                                                'creator': x.creator,
                                                'content': x.content})

            self.render("blog.html", data={'posts': posts,
                        'comments': comment_list, 'username': username})
        else:
            self.redirect('/login')


"""
resgistration class for path /signup
"""


class RegisterHandler(MainHandler):
    def get(self):
        self.render('register.html', data={})

    def post(self):
        mismatch = False  # mistach is True if the two passwords arent equals
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')
        exists = False

        # check if user already in db (means, user already exists)
        v = Users.all().filter('name =', username)
        if v.get():
            exists = True
        # if user does not exist, verify inputs for validation
        else:
            if (email):
                # compile to check regular expression pattern
                p = re.compile('^[\S]+@[\S]+.[\S]+$')
                # check if email matchs the pattern,
                # if no retunr None to email var
                email = p.match(email)

                if email:
                    email = True
                else:
                    email = 'invalid'
            if 21 > len(password) > 2:
                if password != verify:
                    mismatch = True
            else:
                password = False
            if (' ' in username):
                username = True
            else:
                if 21 > len(username) > 2:
                    username = False
                else:
                    username = True
        # if one or more inputs are invalid resend the register
        # page to the user with the email(if present)
        # and the name firstly typed
        if (exists or mismatch or
                username or (not password) or email == 'invalid'):
            self.render('register.html',
                        data={'username': self.request.get('username'),
                              'email': self.request.get('email'),
                              'mismatch': mismatch,
                              'usernameInvalid': username,
                              'password': password, 'emailValid': email,
                              'exists': exists})
        # if all enters a valid, register user in db
        else:
            username = str(self.request.get("username"))
            password = str(self.request.get("password"))
            password = self.hash_pass(password)
            usuario = Users(name=username, password=password)
            usuario = usuario.put()
            self.set_cookie('user_id', usuario.id())
            self.set_cookie('username', username)
            time.sleep(0.1)
            self.redirect('/')


"""
login class for /login
"""


class LoginHandler(MainHandler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        v = Users.all().filter('name =', username)
        if v.get():
            db_pass = v.get().password
        if v.get() and (db_pass ==
           self.hash_pass(password, db_pass.split('|')[0])):
            user_id = v.get().key().id()
            self.set_cookie('user_id', user_id)
            self.set_cookie('username', username)
            self.redirect('/')
        else:
            self.render('login.html', invalid=True)


"""
logout class to logout user /logout
"""


class LogoutHandler(MainHandler):
    def get(self):
        self.logout()


"""
class to create a new post /newpost
"""


class NewPostHandler(MainHandler):
    def get(self):
        if self.check():
            self.render('newpost.html')
        else:
            self.redirect('/login')

    def post(self):
        if self.check():
            data = json.loads(self.request.body)
            title = data['title']
            postdata = data['content']
            user_id = self.check()
            post = Post(title=title,
                        content=postdata, creator=user_id)
            post.put()
            self.response.write('haribol, postou')
        else:
            self.redirect('/login')


"""
class to edit post /edit
"""


class EditPost(MainHandler):
    def get(self):
        if self.check():
            creator_id = self.request.get('creator_id')
            post_id = self.request.get('post_id')
            post_title = self.request.get('title')
            post_content = self.request.get('content')
            data = {'creator': creator_id, 'id': post_id,
                    'title': post_title, 'content': post_content}
            if self.check_user(creator_id):
                self.render('editpost.html', data=data)
            else:
                self.redirect('/')
        else:
            self.redirect('/login')

    def post(self):
        if self.check():
            data = json.loads(self.request.body)
            creator = data['creator']
            if self.check_user(creator):                
                title = data['title']
                postdata = data['content']
                user_id = self.check()
                post_id = data['post_id']
                # used to retrieve an key for the entity
                post_key = db.Key.from_path('Post', int(post_id))
                post = db.get(post_key)  # from the key, get the entity
                post.title = title
                post.content = postdata
                post.creator = user_id
                post.put()
                self.response.write('edited sucessfully')
        else:
            self.redirect('/login')

"""
class comment, is the /comment endpoint
that handlers $.ajax data with new comment
"""


class CommentHandler(MainHandler):
    def post(self):
        data = json.loads(self.request.body)
        user_id = self.check()[1]
        comment = data['content']
        post_id = data['post_id']
        new_comment = Comments(creator=str(user_id),
                               content=comment,
                               post_id=str(post_id))
        comment_key = new_comment.put()
        comment_id = comment_key.id()
        # put comment id into comments list on Post entity
        post_key = db.Key.from_path('Post', int(post_id))
        new_comment = db.get(post_key)
        new_comment.comments.insert(0, str(comment_id))
        new_comment.put()
        # finihs of putting comments id into comments list on Post object
        self.response.write('Haribol, deu certo')


app = webapp2.WSGIApplication([('/', MainPage), ('/signup', RegisterHandler),
                               ('/login', LoginHandler),
                               ('/logout', LogoutHandler),
                               ('/newpost', NewPostHandler),
                               ('/edit', EditPost),
                               ('/comment', CommentHandler)
                               ], debug=True)

