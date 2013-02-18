# stdlib imports
import logging

# third-party imports
from google.appengine.api import users
from google.appengine.ext import ndb

# local imports
from forms.forms import CommentForm
from forms.forms import TaskForm
from forms.forms import add_user_to_task_form
from forms.forms import completion_task_form
from forms.forms import reassign_task_form
from handlers.base import TemplateHandler
from handlers.auth import AuthedTemplateHandler
from models.comment import Comment
from models.history import add_to_history
from models.task import Task
from utils.auth import authed_for_task
from utils.auth import is_admin


class IndexHandler(TemplateHandler):

    """
    Serves the index page shown to all unauthenticated users
    """

    def get(self):

        # redirect to projects page if already logged in
        if users.get_current_user() is not None:
            redirect_url = self.uri_for('projects')
            return self.redirect(redirect_url)

        # render and return login page
        return self.render_response('login.html', {})


class ProjectHandler(AuthedTemplateHandler):

    """
    Shows all of a users projects in a list, or all
    projects if an admin user
    """

    def handle_get(self):

        # base projects query
        projects = Task.query().filter(Task.is_top_level == True)

        # filter projects if user is not an admin
        if not is_admin(self.user_entity):
            projects = projects.filter(Task.users == self.user_entity.key)

        # sort projects by creation date
        projects = projects.order(Task.creation_time)
        # do a keys only query and pull actual objects by key for cache purposes
        projects = [x.get() for x in projects.iter(keys_only=True)]

        # add projects to the template context
        context = {'projects': projects}
        # render and return login page
        return self.render_response('projects.html', context)


class ViewTaskHandler(AuthedTemplateHandler):

    """
    Displays an individual task with all the metadata
    and forms required to interact with it.
    """

    def handle_get(self, task_id):

        # get task from datastore using ID passed in URL
        task_key = ndb.Key(urlsafe=task_id)
        task = task_key.get()
        # throw 404 if task not found
        if task_key is None or task is None:
            return self.abort(404, detail='Task not found: %s' % task_id)

        # check if user is authed to view task
        if not authed_for_task(task, self.user_entity):
            return self.abort(401)

        # check whether or not to offset the list of comments
        from_comment = self.request.get('from_comment', default_value=None)
        # get subtasks from datastore
        subtasks = ndb.get_multi(task.subtasks)
        # get list of users from datastore
        task_users = ndb.get_multi(task.users)
        # form to allow altering of completion status
        completion_form = completion_task_form(task, self.request.POST)
        # form to allow adding comments
        comment_form = CommentForm()
        # for to allow reassigning of task
        reassign_form = reassign_task_form(task, self.request.POST)
        # form to allow adding users to projects
        add_user_form = add_user_to_task_form(task, self.request.POST)
        # add all required objects to context dict
        context = {
            'task': task,
            'subtasks': subtasks,
            'comment_form': comment_form,
            'reassign_form': reassign_form,
            'task_users': task_users,
            'completion_form': completion_form,
            'from_comment': from_comment,
            'add_user_form': add_user_form,
        }
        # render template and return
        return self.render_response('task.html', context)


class AddTaskHandler(AuthedTemplateHandler):

    """
    Form to allow adding a new task
    """

    def handle_get(self, task_id):

        # create new task (with parent)
        parent_task_key = ndb.Key(urlsafe=task_id)
        task = Task(parent=parent_task_key)

        # check if user is authed to add task
        if not authed_for_task(parent_task_key.get(), self.user_entity):
            return self.abort(401)

        # init form object with POST data
        form = TaskForm(self.request.POST)
        # if form was posted and it validates
        if self.request.method == 'POST' and form.validate():
            # build task from form and save
            form.populate_obj(task)
            task.put()
            history_text = 'Task added'
            add_to_history(task, self.user_entity, history_text)
            # build url to redirect to and issue 302 to browser
            redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
            return self.redirect(redirect_url)
        # render form and return (rendering errors if necessary)
        return self.render_response('task_form.html', {'form': form, 'task_or_project': 'task'})


class ReassignTaskHandler(AuthedTemplateHandler):

    """
    POST handler to allow reassigning task
    """

    def handle_get(self, task_id):

        # get task from datastore
        task_key = ndb.Key(urlsafe=task_id)
        task = task_key.get()

        # check if user is authed to reassign task
        if not authed_for_task(task, self.user_entity):
            return self.abort(401)

        # build form with POST data
        form = reassign_task_form(task, self.request.POST, with_default=False)
        # check if form validates
        if form.validate():
            # coerce form data into valid datastore data
            if form.assigned_to.data == 'None':
                data = None
            else:
                data = ndb.Key(urlsafe=form.assigned_to.data)
            # reassign task
            if task.assigned_to is None:
                from_user = 'none'
            else:
                from_user = task.assigned_to.get().given_name
            if data is None:
                to_user = 'none'
            else:
                to_user = data.get().given_name
            history_text = 'Task reassigned from %s to %s' % (from_user, to_user)
            task.assigned_to = data
            # store task
            task.put()
            add_to_history(task, self.user_entity, history_text)
        else:
            # log on form error
            logging.error(form.errors)
        # build url of task and redirect to it
        redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
        return self.redirect(redirect_url)


class CompletionTaskHandler(AuthedTemplateHandler):

    """
    Form to allow altering completion status of tasks
    """

    def handle_get(self, task_id):

        # get task from datastore
        task_key = ndb.Key(urlsafe=task_id)
        task = task_key.get()

        # check if user is authed to reassign task
        if not authed_for_task(task, self.user_entity):
            return self.abort(401)

        # build form with POST data
        form = completion_task_form(task, self.request.POST, with_default=False)
        # check if form validates
        if form.validate():
            # get original status before changing
            from_status = task.task_completion_status
            # populate task from form and save
            form.populate_obj(task)
            task.put()
            # add history record
            to_status = form.task_completion_status.data
            history_text = 'Task completion status changed from %d to %d' % (from_status, to_status)
            add_to_history(task, self.user_entity, history_text)
            # add a flash message to session
            self.session.add_flash("Completion status changed to %d" % task.completion_status)
        else:
            # log if validation error
            logging.error(form.errors)
        # build redirect url and return
        redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
        return self.redirect(redirect_url)


class AddCommentHandler(AuthedTemplateHandler):

    """
    Form to allow adding a comment to a task
    """

    def handle_get(self, task_id):

        # create new task (with parent)
        task_key = ndb.Key(urlsafe=task_id)

        # check if user is authed to reassign task
        if not authed_for_task(task_key.get(), self.user_entity):
            return self.abort(401)

        # get user key
        user_key = self.user_entity.key
        # create new comment object
        comment = Comment(parent=task_key)

        # populate form with POST data
        form = CommentForm(self.request.POST)
        if form.validate():
            # populate comment object with validated form data
            form.populate_obj(comment)
            # set reference properties on comment object
            comment.task = task_key
            comment.user = user_key
            # store comment
            comment.put()
            # record history item
            history_text = 'Comment added'
            add_to_history(task_key.get(), self.user_entity, history_text)
        else:
            # log on validation error
            logging.error(form.errors)

        # redirect to task view page
        redirect_url = self.uri_for('task-view', task_id=task_key.urlsafe())
        return self.redirect(redirect_url)
