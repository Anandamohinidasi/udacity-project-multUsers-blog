import os
import jinja2
import webapp2
import string
import hmac
import random
import operator 
import time
import json
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))

"""
  class Handler is the main class that Handler jinjas templates, it ehreit from webapp2
"""
class MainHandler(webapp2.RequestHandler):
    def write(self, *a, **kw): 
	self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)
    def render(self, template, **kw):
	self.write(self.render_str(template, **kw))
	
    # generate an random salt 
    def generate_salt(self):
	return ''.join(random.choice(string.lowercase) for a in xrange(5))

    # method for password hash
    def hash_pass(self,password, salt = None):
	if not salt:  # this allows has_pass to be used for verification also
		salt = self.generate_salt()  # if no salt gived, generate a new salt
	return "%s|%s" % (salt, hmac.new('haribol', password+salt).hexdigest())

    #method to check if user is already logged in
    def check(self):
	cookie = self.request.cookies.get('user_id')
	if cookie:
		if cookie == self.hash_id(cookie.split('|')[0]):
			return cookie
		return None
	else:
		return None

    # method to hash user id before sending it to cookie
    def hash_id(self, user_id):
	return '%s|%s' % (str(user_id), hmac.new('haribol', str(user_id)).hexdigest())

    # method to set a cookie 
    def set_cookie(self, name, value):
	if value:
		value = self.hash_id(value)
		self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name,value))
	else:
	  	self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name,value))  # if no value means cookie should be empty, i.e logout function	
    
    # method to register the user 
    def register(self, name, password):
	pass

    # method to login user 
    def login(self, name, password):
	self.redirect('/welcome')
   
    # method to logout user 
    def logout(self):
 	self.set_cookie('user_id', '')
	self.redirect('/signup')
  
    # method to make user post 
    def post(self, id, post):
	pass
	
    # method to check if the user triyng to edit the post
    # is the same user who once created it
    def check_user(self,creator_id):
	if creator_id == self.check().split('|')[0]:
		return True
	return False
	
# Post class is a new identitie at Google App Engine Datastore
class Post(db.Model):
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    creator = db.StringProperty(required = True)
    likes = db.IntegerProperty(default=0)
    comments = db.ListProperty(item_type= str)	

# Post class is a new identitie at Google App Engine Datastore
class Users(db.Model):
    name = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.EmailProperty()	

# Comments class, where comments are stored
class Comments(db.Model):
	creator = db.StringProperty(required=True)
	content = db.TextProperty(required = True)
	post_id = db.StringProperty(required = True)  
	created = db.DateTimeProperty(auto_now_add = True)	

# main class for path '/'   
class MainPage(MainHandler):    	
    def get(self):
	check = self.check()
	if check:	
		if self.request.get('like'):
			post_id = self.request.get('post_id')
			post_key = db.Key.from_path('Post', int(post_id))  # used to retrieve an key for the entity
			post = db.get(post_key)
			print 'foi check eh: %s \n e o creator foi %s' % (check, post.creator) 
			if not self.check_user(post.creator):			
				if post.likes:
					post.likes = post.likes + 1
				else:
					post.likes = 1
				post.put()
				time.sleep(0.1)
				self.redirect('/')
			else:
				self.redirect('/')
		posts = Post.all().order('-created')
		comments = Comments.all().order('-created')
		comment_list = []
		for a in posts:
			for b in a.comments:
				for x in comments:
					print b
					print x.key().id()
					if str(b) == str(x.key().id()):
						comment_list.append({'post': a.key().id(), 'creator': x.creator,'content':x.content})
		print comment_list
				
		self.render("blog.html", data = {'posts': posts, 'comments': comment_list }) 
	else:
		self.redirect('/signup')

    def post(self):
	pass

# resgistration class for path /signup
class RegisterHandler(MainHandler):

    def get(self):
	self.render('register.html', data={})

    def post(self):
	mismatch = False # mistach is True if the two passwords arent equals
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
			email = p.match(email) # check if email matchs the pattern, if no retunr None to email var
			if email:
				email = True
			else:
				email = 'invalid'
		if 21>len(password)>2:
			if password!=verify:
				mismatch = True
		else:
			password = False
		if (' ' in username):
			username = True
		else:
			if 21>len(username)>2:
				username = False
			else:
				username = True
	# if one or more inputs are invalid resend the register page to the user with the email(if present) 
	# and the name firstly typed
	if (exists == True or mismatch == True or username == True or password == False or email=='invalid'):
		self.render('register.html', data = {'username': self.request.get('username'), 
						'email': self.request.get('email'), 'mismatch': mismatch, 
						'usernameInvalid': username,
						'password': password, 'emailValid': email, 'exists': exists})
	# if all enters a valid, register user in db	
	else:	
		username = str(self.request.get("username"))
		password =  str(self.request.get("password"))
		password = self.hash_pass(password)
		usuario = Users(name = username, password = password)
		usuario = usuario.put()
		self.set_cookie('user_id', usuario.id())
		time.sleep(0.1)
		self.redirect('/')


# login class for /login   
class LoginHandler(MainHandler):
        def get(self):
	                self.render('login.html')

	def post(self):
			username = self.request.get('username')
			password = self.request.get('password')
			v = Users.all().filter('name =', username)
			if v.get():
				db_pass = v.get().password
			
			if v.get() and (db_pass == self.hash_pass(password,db_pass.split('|')[0])):
				user_id = v.get().key().id()
				self.set_cookie('user_id', user_id)
				self.redirect('/')
			else:		
				print 'analisou e nao aprovou'
				self.render('login.html', invalid = True)	 


# logout class to logout user /logout
class LogoutHandler(MainHandler):
	def get(self):
		self.logout() 

# class to create a new post /newpost
class NewPostHandler(MainHandler):
	def get(self):
		if self.check():
			self.render('newpost.html')
		else:
			self.redirect('/signup')
	def post(self):
		title = self.request.get('title')
		postdata = self.request.get('postarea')
		user_id = self.check().split('|')[0]
		post = Post(title = title, content = postdata, creator = user_id)
		post.put()
		time.sleep(0.1)
		self.redirect('/')

# class to edit post
class EditPost(MainHandler):
	def get(self):
		if self.check():
			creator_id = self.request.get('creator_id')
			post_id = self.request.get('post_id')
			post_title = self.request.get('title')
			post_content = self.request.get('content')
			data = { 'creator': creator_id, 'id': post_id, 'title': post_title, 'content': post_content}
			if self.check_user(creator_id):
				self.render('editpost.html', data = data)
			else:
				self.redirect('/')
		else:
			self.redirect('/signup')
	def post(self):
		title = self.request.get('title')
		postdata = self.request.get('postarea')
		user_id = self.check().split('|')[0]
		post_id = self.request.get('id')
		post_key = db.Key.from_path('Post', int(post_id))  # used to retrieve an key for the entity
		post = db.get(post_key)  # from the key, get the entity
		post.title = title
		post.content = postdata
		post.creator = user_id
		post.put()
		time.sleep(0.1)
		self.redirect('/')		 
# class comment, is the /comment endpoint that handlers $.ajax data with new comment
class CommentHandler(MainHandler):
	def post(self):
		data = json.loads(self.request.body)
		user_id = self.check().split('|')[0]
		comment = data['content']
		post_id = data['post_id']
		new_comment = Comments(creator = str(user_id), content = comment, post_id= str(post_id))
		comment_key = new_comment.put()
		comment_id = comment_key.id()

		# put comment id into comments list on Post entity
		post_key = db.Key.from_path('Post', int(post_id))
		new_comment = db.get(post_key)
		new_comment.comments.append(str(comment_id))
		new_comment.put()
		# finihs of putting comments id into comments list on Post object
		self.response.write('Haribol, deu certo')
  
app = webapp2.WSGIApplication([
    ('/', MainPage), ('/signup', RegisterHandler), ('/login', LoginHandler), ('/logout', LogoutHandler), ('/newpost', NewPostHandler), ('/edit', EditPost), ('/comment', CommentHandler)
], debug=True)


