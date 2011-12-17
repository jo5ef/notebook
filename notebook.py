from google.appengine.ext import webapp
import os
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

def authenticate(requestHandler):
	user = users.get_current_user()
	if not user:
		requestHandler.redirect(users.create_login_url(requestHandler.request.uri))
	return user

def render_template(requestHandler, path, data):
	p = os.path.join(os.path.dirname(__file__), path)
	requestHandler.response.out.write(template.render(p, data))

class Note(db.Model):
	user = db.UserProperty()
	body = db.TextProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	tags = db.StringListProperty()
	
	def tagsval(self):
		return ' '.join(self.tags)

class Notes(webapp.RequestHandler):
	
	def get(self, noteId):
		user = authenticate(self)
		if not user: return
		
		note = Note.get_by_id(int(noteId)) if noteId else None
		if note and note.user != user:
			self.error(403)
			return
		
		render_template(self, 'templates/note.html', {
			'user': user,
			'note': note,
		})

	def post(self, noteId):
		user = authenticate(self)
		if not user: return
		
		note = Note.get_by_id(int(noteId)) if noteId else Note(user=user)
		
		if not note:
			self.error(404)
			return
		
		if note.user and note.user != user:
			self.error(403)
			return
		
		note.body = self.request.get('body')
		note.tags = self.request.get('tags').split(' ')
		note.put()
		self.redirect('/')

class MainPage(webapp.RequestHandler):
	def get(self):
		user = authenticate(self)
		if not user: return
		
		notes = Note.all()
		notes.filter('user =', user)
		
		if self.request.get('q'):
			notes.filter('tags =', self.request.get('q'))
			
		notes.order('-date')
		
		render_template(self, 'templates/index.html', {
			'user': user,
			'notes': notes.fetch(50),
		})

application = webapp.WSGIApplication([
	('/', MainPage),
	('/notes/(\d*)', Notes)
], debug = True)

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()
