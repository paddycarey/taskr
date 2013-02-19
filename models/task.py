# third-party imports
from google.appengine.ext import ndb

# local imports
from models.base import BaseModel
from models.comment import Comment
from models.history import History


class Task(BaseModel):

    """
    Task is the central model for all of taskr. Projects
    and tasks are only distinguished from each other at
    the UI level, internally, a project is simply a task
    without a parent.

    This model contains only a few user editable properties,
    most are computed automatically on save.
    """

    # Name and description of task
    name = ndb.StringProperty()
    description = ndb.StringProperty(indexed=False)

    # who is this task currently assigned to
    assigned_to = ndb.KeyProperty(kind='User')

    # if this task is top-level then we can assign users to it
    users = ndb.KeyProperty(repeated=True)

    # these fields are user settable but will be completely ignored if
    # this entity has any subtasks
    task_time_estimate = ndb.IntegerProperty(default=0)
    task_completion_status = ndb.IntegerProperty(default=0, choices=range(101))

    ##################################################
    # Computed Properties should not be set by users #
    ##################################################

    # task's parent
    supertask = ndb.KeyProperty()

    def _completion_status(self):
        # return this task's own completion status if no subtasks
        if not self.subtasks:
            return self.task_completion_status
        # calculate avg of completion status of subtasks
        subtask_completion = [x.get().completion_status for x in self.subtasks]
        subtask_completion = [float(x) for x in subtask_completion]
        subtask_completion_avg = sum(subtask_completion) / len(subtask_completion)
        return round(int(subtask_completion_avg) / 2.0, -1) * 2
    completion_status = ndb.ComputedProperty(_completion_status)

    # estimate of time required to complete task
    def _time_estimate(self):
        # return this task's own time estimate if no subtasks
        if not self.subtasks:
            return self.task_time_estimate
        # return sum of time estimates for all immediate subtasks
        subtask_time_estimate = sum([x.get().time_estimate for x in self.subtasks])
        return subtask_time_estimate
    time_estimate = ndb.ComputedProperty(_time_estimate)

    # list of subtasks for this project
    def _subtasks(self):
        # perform ancestor query to get list of subtask keys for this entity
        q = Task.query(ancestor=self.key)
        q = q.filter(Task.supertask == self.key)
        return [s for s in q.iter(keys_only=True)]
    subtasks = ndb.KeyProperty(repeated=True)

    # simple count to make num of subtasks queryable
    def _subtasks_count(self):
        return len(self.subtasks)
    subtasks_count = ndb.IntegerProperty()

    # indicate if this task is top-level (i.e. a project)
    def _is_top_level(self):
        return self.supertask is None
    is_top_level = ndb.ComputedProperty(_is_top_level)

    # count the number of comments for this task
    def _comments_count(self):
        q = Comment.query(ancestor=self.key)
        q = q.filter(Comment.task == self.key)
        return q.count()
    comments_count = ndb.IntegerProperty(default=0)

    # key of the project this task belongs to
    def _project(self):
        key = self.key
        while True:
            if key is None or key.parent() is None:
                break
            key = key.parent()
        return key
    project = ndb.ComputedProperty(_project)

    # query that'll retrieve 5 comments from the
    # datastore for this task, starting at the
    # specified ID, or at the start if no ID is specified
    def comments(self):
        q = Comment.query(ancestor=self.key)
        q = q.filter(Comment.task == self.key)
        q = q.order(-Comment.creation_time)
        return q

    ######################################
    # Helper functions to perform common #
    # repetitive actions for tasks       #
    ######################################

    # List of dicts that can be used to display breadcrumbs
    # for a particular task
    def breadcrumbs(self):
        key = self.key
        crumbs = []
        while True:
            key = key.parent()
            if key is None:
                break
            entity = key.get()
            crumbs.append({'name': entity.name, 'task_id': key.urlsafe()})
        return reversed(crumbs)

    @property
    def history(self):
        q = History.query(ancestor=self.key)
        q = q.order(-History.creation_time)
        return [h.get() for h in q.iter(limit=10, keys_only=True)]

    def put(self, *args, **kwargs):

        """
        Override put() so that we can assign some extra
        values that can't be assigned as ComputedProperties
        due to requiring a valid key.
        """

        # save entity as normal
        super(Task, self).put(*args, **kwargs)
        # make task's parent queryable
        self.supertask = self.key.parent()
        # find this tasks's subtasks and count them
        self.subtasks = self._subtasks()
        self.subtasks_count = self._subtasks_count()
        self.comments_count = self._comments_count()
        # save the task again
        super(Task, self).put(*args, **kwargs)
        # if this task has a parent then save it too,
        # which'll cause it's computed properties to
        # be recalculated.  This should bubble up all
        # the way to project level
        if self.supertask is not None:
            supertask = self.supertask.get()
            supertask.put()
