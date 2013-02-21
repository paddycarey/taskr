# third-party imports
from webapp2 import Route
from webapp2_extras.routes import RedirectRoute


ROUTES = [

    #####################
    # Admin only routes #
    #####################

    RedirectRoute(
        r'/t/new/',
        'handlers.template.forms.AddProjectHandler',
        name="project-add",
        handler_method='handle',
        strict_slash=True,
        methods=['GET', 'POST'],
    ),

    RedirectRoute(
        r'/t/<task_id>/add_user/',
        'handlers.template.forms.AddUserToProjectHandler',
        name="task-add-user",
        handler_method='post',
        strict_slash=True,
        methods=['POST'],
    ),

    RedirectRoute(
        r'/t/<task_id>/remove_user/<user_id>/',
        'handlers.template.forms.RemoveUserFromProjectHandler',
        name="task-remove-user",
        strict_slash=True,
    ),

    ####################################
    # User facing template/form routes #
    ####################################

    Route(
        r'/',
        'handlers.template.general.IndexHandler',
        name="user-template-index"
    ),

    RedirectRoute(
        r'/t/',
        'handlers.template.task.ProjectHandler',
        name="projects",
        strict_slash=True,
    ),

    RedirectRoute(
        r'/t/<task_id>/',
        'handlers.template.task.ViewTaskHandler',
        name="task-view",
        strict_slash=True,
    ),

    RedirectRoute(
        r'/t/<task_id>/new/',
        'handlers.template.forms.AddTaskHandler',
        name="task-add",
        handler_method='handle',
        strict_slash=True,
        methods=['GET', 'POST'],
    ),

    RedirectRoute(
        r'/t/<task_id>/edit/',
        'handlers.template.forms.EditTaskHandler',
        name="task-edit",
        handler_method='handle',
        strict_slash=True,
        methods=['GET', 'POST'],
    ),

    RedirectRoute(
        r'/t/<task_id>/reassign/',
        'handlers.template.forms.ReassignTaskHandler',
        name="task-reassign",
        strict_slash=True,
    ),

    RedirectRoute(
        r'/t/<task_id>/completion/',
        'handlers.template.forms.ChangeCompletionStatusTaskHandler',
        name="task-completion",
        strict_slash=True,
    ),

    RedirectRoute(
        r'/t/<task_id>/comment/',
        'handlers.template.forms.AddCommentHandler',
        name="task-comment",
        strict_slash=True,
    ),

    RedirectRoute(
        r'/t/<task_id>/comment/<comment_id>/delete/',
        'handlers.template.forms.DeleteCommentHandler',
        name="task-comment-delete",
        strict_slash=True,
    ),

    RedirectRoute(
        r'/t/<task_id>/<comment_cursor>/',
        'handlers.template.task.ViewTaskHandler',
        name="task-view-comment-page",
        strict_slash=True,
    ),

    #############################
    # Auth/Login related routes #
    #############################

    Route(
        r'/update_profile',
        'handlers.template.profile.UpdateProfileHandler',
        name="update-profile"
    ),

    Route(
        r'/auth_callback',
        'handlers.template.auth.CallbackHandler',
        name="oauth-callback"
    ),

]
