# third-party imports
from google.appengine.api import users


def is_admin(user):

    # check if the currently logged in user
    # is an admin of the app on appengine
    if users.is_current_user_admin():
        return True

    # check if passed user is marked as a local admin
    if user.is_admin:
        return True

    return False


def authed_for_task(task, user):

    # check if user is an admin
    if is_admin(user):
        return True

    # check if user has permissions for this task
    if user.key in task.project.get().users:
        return True

    return False
