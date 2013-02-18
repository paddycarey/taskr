# third-party imports
from wtforms import Form
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import TextField
from wtforms import TextAreaField
from wtforms import validators

# local imports
from models.auth import User


class TaskForm(Form):

    """
    Form to allow adding tasks
    """

    # name of task
    name = TextField('Name', [validators.Length(min=3, max=255)])
    # long description of task
    description = TextAreaField('Description', [validators.Length(min=6, max=5000)])
    # time estimate for task
    task_time_estimate = IntegerField('Time Estimate', description="In minutes")


class CommentForm(Form):

    """Form to allow adding comments to tasks"""

    comment = TextAreaField('Comment', [validators.Length(min=2, max=5000)])


def add_user_to_task_form(task, post_data):

    """
    Factory function to allow building of selectfield
    only forms for adding users to tasks
    """

    def choices():
        # choices for select field
        all_users = User.query().order(User.family_name).iter(keys_only=True)
        task_users = task.project.get().users
        fhoices = [(uk.urlsafe(), uk.get().given_name + ' ' + uk.get().family_name) for uk in all_users if not uk in task_users]
        fhoices = [('None', '--------')] + fhoices
        return fhoices

    class AddUserToTaskForm(Form):

        """
        Form to allow adding users to tasks
        """

        # user task is assigned to
        user = SelectField(u'Add user to task', choices=choices())

    # init form
    form = AddUserToTaskForm(post_data)

    # return form
    return form


def reassign_task_form(task, post_data, with_default=True):

    """
    Factory function to allow building of selectfield
    only forms for reassigning tasks
    """

    class ReassignTaskForm(Form):

        """
        Form to allow reassigning of tasks
        """

        # user task is assigned to
        assigned_to = SelectField(u'Assigned to')

        def __init__(self, formdata=None, obj=None, prefix='', assign_default=True, **kwargs):

            """
            Override init to provide default data to form
            """

            if assign_default:
                kwargs.setdefault('assigned_to', self.default())
            Form.__init__(self, formdata, obj, prefix, **kwargs)
            self.assigned_to.choices = self.choices()

        def choices(self):
            # choices for select field
            users = task.project.get().users
            fhoices = [(uk.urlsafe(), uk.get().given_name + ' ' + uk.get().family_name) for uk in users]
            fhoices = [('None', '--------')] + fhoices
            return fhoices

        def default(self):
            # default choice for select field
            fefault = task.assigned_to
            if fefault is not None:
                fefault = fefault.urlsafe()
            return fefault

    # init form
    form = ReassignTaskForm(post_data, assign_default=with_default)

    # return form
    return form


def completion_task_form(task, post_data, with_default=True):

    """
    Factory function to allow building of selectfield
    only forms for altering the completion status of tasks
    """

    class CompletionTaskForm(Form):

        """
        Form to allow altering the completion status of tasks
        """

        # completion % of task
        task_completion_status = SelectField(u'Completion (%)', coerce=int)

        def __init__(self, formdata=None, obj=None, prefix='', assign_default=True, **kwargs):

            """
            Override init to provide default data to form
            """

            if assign_default:
                kwargs.setdefault('task_completion_status', task.completion_status)
            Form.__init__(self, formdata, obj, prefix, **kwargs)
            self.task_completion_status.choices = self.choices()

        def choices(self):
            # choices for select field
            fhoices = [
                (0, ' 0%: Not started'),
                (20, '20%: Started'),
                (40, '40%: Implementing'),
                (60, '60%: Debugging/Bugfixing'),
                (80, '80%: Ready for review'),
                (100, '100%: Completed'),
            ]
            return fhoices

    # init form
    form = CompletionTaskForm(post_data, assign_default=with_default)

    # return form
    return form
