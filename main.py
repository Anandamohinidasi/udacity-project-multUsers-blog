import os
import jinja2
import webapp2
import string

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw): 
	self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)
    def render(self, template, **kw):
	self.write(self.render_str(template, **kw))
class MainPage(Handler):    	
    def encode(self, code):
	self.alfabeto = string.ascii_lowercase
	c = list(code)
	print len(self.alfabeto)
	print self.alfabeto
	for a in c:
	    i = c.index(a)
	    if a=="\n" or a=="\r":
		print "encontrei um enter "
		# c[i] = "\n"
		continue
	    elif a==" ":
		c[i] = " "
		continue
	    else:
	        x = self.alfabeto.find(a) + 13 
	        print 'valor de x: ', x, 'valor de a: ', a       
	        if x>25:
	    	    x= x-26;
	            c[i] = self.alfabeto[x]
	        else:		    
	            c[i] = self.alfabeto[x]
 	        print 'code depois do replace: ', c
	code = "".join(c)
        return code
    def get(self):
        self.render("shopping_list.html")
    def post(self):
	code= self.request.get('text')
	encode = self.encode(code)
	self.render("shopping_list.html", encoded=encode)
        
class Encode(Handler):
    def get(self, code):
        self.render("shopping_list.html", encoded=code)
   
	 
app = webapp2.WSGIApplication([
    ('/', MainPage),('/enconde', Encode)
], debug=True)

