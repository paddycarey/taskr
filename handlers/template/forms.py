# marty mcfly imports
from __future__ import absolute_import

# third-party imports
from google.appengine.ext import ndb

# local imports
from forms.forms import CommentForm
from forms.forms import TaskForm
from forms.forms import add_user_to_task_form
from forms.forms import completion_task_form
from forms.forms import reassign_task_form
from handlers.template.auth import AuthedTemplateHandler
from models.comment import Comment
from models.history import add_to_history
from models.task import Task
from utils.auth import authed_for_task
from utils.auth import is_admin


##################################
# Admin only form handlers first #
##################################


class AddProjectHandler(AuthedTemplateHandler):

    """
    Form handler to allow admin users to add new top-level
    tasks (projects) to the datastore.
    """

    def handle(self):

        # check if user has admin permissions
        if not is_admin(self.user_entity):
            return self.abort(401, detail="Admin permissions required")

        # populate form with POST data (if available)
        form = TaskForm(self.request.POST)

        # check if form was POSTed and that user input validates
        if self.request.method == 'POST' and form.validate():

            # create new project
            task = Task()

            # populate task from form
            form.populate_obj(task)
            # add user to project's user list and assign to self
            task.users.append(self.user_entity.key)
            task.assigned_to = self.user_entity.key
            # store task in datastore
            task.put()

            # record history item
            history_text = 'Project added'
            add_to_history(task, self.user_entity, history_text)
            self.session.add_flash(history_text)

            # redirect to task view on succesful save
            redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
            return self.redirect(redirect_url)

        # render form and display
        context = {'form': form, 'task_or_project': 'project', 'add_or_edit': 'Add new'}
        return self.render_response('task_form.html', context)


class AddUserToProjectHandler(AuthedTemplateHandler):

    """
    POST handler to allow adding users to
    projects (gives read/write permissions to user)
    """

    def post(self, task_id):

        # check if user has admin permissions
        if not is_admin(self.user_entity):
            return self.abort(401, detail="Admin permissions required")

        # get task from datastore
        task_key = ndb.Key(urlsafe=task_id)
        task = task_key.get()

        # if this isn't a project then we can't add users to it
        if not task.is_top_level:
            return self.abort(403, detail="Cannot add a user to a subtask")

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
            self.session.add_flash(history_text)

        else:

            # if form doesn't validate then add a flash message before redirecting
            flash_msg = form.errors
            self.session.add_flash(flash_msg)

        # build url of task and redirect to it
        redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
        return self.redirect(redirect_url)


#############################
# User-facing form handlers #
#############################


class AddTaskHandler(AuthedTemplateHandler):

    """
    Form to allow adding a new task
    """

    def handle(self, task_id):

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

            # add history record for this task
            history_text = 'Task added'
            add_to_history(task, self.user_entity, history_text)
            self.session.add_flash(history_text)

            # build url to redirect to and issue 302 to browser
            redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
            return self.redirect(redirect_url)

        # render form and return (rendering errors if necessary)
        context = {'form': form, 'task_or_project': 'task'}
        return self.render_response('task_form.html', context)


class EditTaskHandler(AuthedTemplateHandler):

    """
    Form handler to allow admin users to add new top-level
    tasks (projects) to the datastore.
    """

    def handle(self, task_id):

        # pull project from datastore or issue 404
        task = ndb.Key(urlsafe=task_id).get()
        if task is None:
            return self.abort(404, 'Project not found')

        # check if user has admin permissions
        if task.is_top_level:
            if not is_admin(self.user_entity):
                return self.abort(401, detail="Admin permissions required")
            task_or_project = 'project'
        else:
            task_or_project = 'task'

        # populate form with POST data (if available)
        form = TaskForm(self.request.POST, task)

        # check if form was POSTed and that user input validates
        if self.request.method == 'POST' and form.validate():

            # populate task from form
            form.populate_obj(task)
            # store task in datastore
            task.put()

            # record history item
            history_text = '%s edited' % task_or_project.capitalize()
            add_to_history(task, self.user_entity, history_text)
            self.session.add_flash(history_text)

            # redirect to task view on succesful save
            redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
            return self.redirect(redirect_url)

        # render form and display
        context = {'form': form, 'task_or_project': task_or_project, 'add_or_edit': 'Editing'}
        return self.render_response('task_form.html', context)


class ReassignTaskHandler(AuthedTemplateHandler):

    """
    POST handler to allow reassigning task to another user
    """

    def post(self, task_id):

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

            # construct history record
            if task.assigned_to is None:
                from_user = 'none'
            else:
                from_user = task.assigned_to.get().given_name
            if data is None:
                to_user = 'none'
            else:
                to_user = data.get().given_name
            history_text = 'Task reassigned from %s to %s' % (from_user, to_user)

            # reassign task
            task.assigned_to = data
            # store task
            task.put()

            # add history record and add flash msg
            add_to_history(task, self.user_entity, history_text)
            self.session.add_flash(history_text)

        else:

            # if form doesn't validate then add a flash message before redirecting
            flash_msg = form.errors
            self.session.add_flash(flash_msg)

        # build url of task and redirect to it
        redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
        return self.redirect(redirect_url)


class ChangeCompletionStatusTaskHandler(AuthedTemplateHandler):

    """
    Form to allow altering completion status of tasks
    """

    def post(self, task_id):

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
            self.session.add_flash(history_text)

        else:

            # if form doesn't validate then add a flash message before redirecting
            flash_msg = form.errors
            self.session.add_flash(flash_msg)

        # build redirect url and return
        redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
        return self.redirect(redirect_url)


class AddCommentHandler(AuthedTemplateHandler):

    """
    Form to allow adding a comment to a task
    """

    def post(self, task_id):

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

            # add a flash message to session
            self.session.add_flash(history_text)

        else:

            # if form doesn't validate then add a flash message before redirecting
            flash_msg = form.errors
            self.session.add_flash(flash_msg)

        # redirect to task view page
        redirect_url = self.uri_for('task-view', task_id=task_key.urlsafe())
        return self.redirect(redirect_url)


class DeleteCommentHandler(AuthedTemplateHandler):

    """
    POST only route allowing to delete comments
    """

    def get(self, task_id, comment_id):

        # reconstruct comment key and pull entity from datastore
        comment_key = ndb.Key(urlsafe=comment_id)
        comment = comment_key.get()
        # pull task from datastore
        task = comment.task.get()

        if not comment.task.urlsafe() == task_id:
            return self.abort(400, detail='Task/Comment mismatch')

        # users can only delete their own comments
        if not self.user_entity.key == comment.user and not is_admin(self.user_entity):
            return self.abort(403, detail="Users can only delete their own comments")

        # delete comment entity
        comment_key.delete()
        # re-save task so as to recalculate all computed
        # fields right the way up to project level
        task.put()

        # add flash msg to indicate success
        self.session.add_flash('Comment successfully deleted')

        # redirect to task view page
        redirect_url = self.uri_for('task-view', task_id=task.key.urlsafe())
        return self.redirect(redirect_url)
