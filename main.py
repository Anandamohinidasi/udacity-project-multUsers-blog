import os
import jinja2
import webapp2
import string
import hmac
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

    # method to set a cookie 
    def set_cookie(self, name, value):
	self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name,value))
    
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

# Post class is a new identitie at Google App Engine Datastore
class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    creator = db.StringProperty(required = True)
    likes = db.StringProperty()
    comments = db.TextProperty()	

# Post class is a new identitie at Google App Engine Datastore
class Users(db.Model):
    name = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.EmailProperty()	
	
# main class for path '/'   
class MainPage(MainHandler):    	
    def get(self):
	self.render("blog.html") # any html

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
		print 'tem'
		exists = True
	# if user does not exist, verify inputs for validation
	else:
		if (email):	
			# compile to check regular expression pattern
			p = re.compile('^[\S]+@[\S]+.[\S]+$')
			email = p.match(email) # check if email matchs the pattern, if no retur None to email var
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
		password = '%s|%s' % (password, hmac.new('haribol', password).hexdigest())
		usuario = Users(name = username, password = password)
		usuario = usuario.put()
		user_id = usuario.id()
		user_id = '%s|%s' % (str(user_id), hmac.new('haribol', str(user_id)).hexdigest())
		self.response.headers.add_header('Set-Cookie', 'user_id=%s, path=/' % user_id)
		self.redirect('/')


# login class for /login   
class LoginHandler(MainHandler):
        def get(self):
	                self.render('login.html')

	def post(self):
			username = self.request.get('username')
			password = self.request.get('password')
			print Users.all().get()
			v = Users.all().filter('name =', username)
			a = Users.all().filter('password =', '%s|%s' % (password,hmac.new('haribol', password).hexdigest()))
			if v.get() and a.get():
				print 'analisou e aprovou, o username eh: %s e a senha eh: %s' % (username,password)
				# users = db.GqlQuery("SELECT * FROM Users where name = %s" % username) 			
				user_id = v.get().key().id()
				user_id = '%s|%s' % (str(user_id), hmac.new('haribol', str(user_id)).hexdigest())			
				self.response.headers.add_header('Set-Cookie', 'user_id=%s, path=/' % user_id)
				self.redirect('/')
			else:		
				print 'analisou e nao aprovou'
				self.render('login.html', invalid = True)	 


# logout class to logout user /logout
class LogoutHandler(MainHandler):
	pass 

app = webapp2.WSGIApplication([
    ('/', MainPage), ('/signup', RegisterHandler), ('/login', LoginHandler), ('/logout', LogoutHandler)
], debug=True)


