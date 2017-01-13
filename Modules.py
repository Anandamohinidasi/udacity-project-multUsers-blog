from google.appengine.ext import db


"""
Post class is a new identitie at Google App Engine Datastore
"""


class Post(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    creator = db.ListProperty(item_type=str, required=True)
    likes = db.ListProperty(item_type=str)
    comments = db.ListProperty(item_type=str)


"""
Post class is a new identitie at Google App Engine Datastore
"""


class Users(db.Model):
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.EmailProperty()


"""
Comments class, where comments are stored
"""


class Comments(db.Model):
    creator = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    post_id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

