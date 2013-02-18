"""
Admin-only handlers (Add project/Edit users/etc.)
"""
# third-party imports
from google.appengine.api import users
from google.appengine.ext import ndb

# local imports
from forms.forms import TaskForm
from forms.forms import add_user_to_task_form
from handlers.auth import AuthedTemplateHandler
from models.history import add_to_history
from models.task import Task


class AdminBaseHandler(AuthedTemplateHandler):

    """
    Performs additional admin credential checks on top of
    the normal user authorisation checks.  Subclassed handlers
    should override the `handle` method to provide functionality.
    """

    def handle_get(self, *args, **kwargs):

        # check if user is admin of the appengine instance
        is_super_admin = users.is_current_user_admin()
        # check if user is local admin
        is_app_admin = self.user_entity.is_admin
        # check that user has at least one or the other
        # type of admin permissions
        is_admin = is_super_admin or is_app_admin

        if not is_admin:
            # throw 401 if user isn't an admin
            return self.abort(401, detail="Admin permissions required")

        # return actual handler method
        return self.handle(*args, **kwargs)


class AddProjectHandler(AdminBaseHandler):

    """
    Form handler to allow admin users to add new top-level
    tasks (projects) to the datastore.
    """

    def handle(self):

        # create new project
        task = Task()

        # populate form with POST data (if available)
        form = TaskForm(self.request.POST)
        # check if form was POSTed and that user input validates
        if self.request.method == 'POST' and form.validate():
            # populate task from form
            form.populate_obj(task)
            task.users.append(self.user_entity.key)
            task.assigned_to = self.user_entity.key
            # store task in datastore
            task.put()
            # record history item
            history_text = 'Project added'
            add_to_history(task, self.user_entity, history_text)
            # redirect to task view on succesful save
            redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
            return self.redirect(redirect_url)
        # render form and display
        return self.render_response('task_form.html', {'form': form, 'task_or_project': 'project'})


class AddUserToTaskHandler(AdminBaseHandler):

    """
    POST handler to allow adding users to tasks
    """

    def handle(self, task_id):

        # get task from datastore
        task_key = ndb.Key(urlsafe=task_id)
        task = task_key.get()

        # if this isn't a project then we can't add users to it
        if not task.is_top_level:
            return self.abort(403)

        # build form with POST data
        form = add_user_to_task_form(task, self.request.POST)
        # check if form validates
        if form.validate() and form.user.data is not None:
            # coerce form data into valid datastore data
            data = ndb.Key(urlsafe=form.user.data)
            # reassign task
            task.users.append(data)
            # store task
            task.put()
            # record history item
            history_text = 'Added user:%s to project' % data.get().given_name
            add_to_history(task, self.user_entity, history_text)
        # build url of task and redirect to it
        redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
        return self.redirect(redirect_url)
