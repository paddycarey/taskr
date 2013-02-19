# marty mcfly imports
from __future__ import absolute_import

# stdlib imports
import logging

# third-party imports
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import ndb

# local imports
from forms.forms import CommentForm
from forms.forms import add_user_to_task_form
from forms.forms import completion_task_form
from forms.forms import reassign_task_form
from handlers.template.auth import AuthedTemplateHandler
from models.task import Task
from utils.auth import authed_for_task
from utils.auth import is_admin


class ProjectHandler(AuthedTemplateHandler):

    """
    Shows all of a users projects in a list, or all
    projects if an admin user
    """

    def get(self):

        @ndb.tasklet
        def get_projects_for_user_async(user_key, admin_permissions):
            # base projects query
            projects = Task.query().filter(Task.is_top_level == True)
            # filter projects if user is not an admin
            if not admin_permissions:
                projects = projects.filter(Task.users == user_key)
            # sort projects by creation date
            projects = projects.order(Task.creation_time)
            project_list = yield projects.map_async(lambda x: x.key)
            raise ndb.Return(project_list)

        # run async query to get projects
        admin_permissions = is_admin(self.user_entity)
        user_key = self.user_entity.key
        projects = get_projects_for_user_async(user_key, admin_permissions)
        # add projects to the template context
        context = {'projects': ndb.get_multi_async(projects.get_result())}
        # render and return login page
        return self.render_response('projects.html', context)


class ViewTaskHandler(AuthedTemplateHandler):

    """
    Displays an individual task with all the metadata
    and forms required to interact with it.
    """

    def get(self, task_id, comment_cursor=None):

        # get task from datastore using ID passed in URL
        task_key = ndb.Key(urlsafe=task_id)
        task = task_key.get()
        # throw 404 if task not found
        if task_key is None or task is None:
            return self.abort(404, detail='Task not found: %s' % task_id)

        # check if user is authed to view task
        if not authed_for_task(task, self.user_entity):
            return self.abort(401, detail="Unauthorised for task")

        # get subtasks from datastore
        subtasks = ndb.get_multi_async(task.subtasks)
        # get list of users from datastore
        task_users = ndb.get_multi_async(task.users)
        # get page of comments
        if comment_cursor is not None:
            comment_cursor = Cursor(urlsafe=comment_cursor)
        comments = task.comments().fetch_page_async(5, start_cursor=comment_cursor)
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
            'comments': comments,
            'comment_cursor': comment_cursor,
            'add_user_form': add_user_form,
        }
        # render template and return
        return self.render_response('task.html', context)
