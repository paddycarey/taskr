# third-party imports
from webapp2 import Route
from webapp2_extras.routes import RedirectRoute


ROUTES = [

    #####################
    # Admin only routes #
    #####################

    RedirectRoute(
        r'/t/new/',
        'handlers.admin.AddProjectHandler',
        name="project-add",
        handler_method='get',
        strict_slash=True,
        methods=['GET', 'POST'],
    ),

    RedirectRoute(
        r'/t/<task_id>/add_user/',
        'handlers.admin.AddUserToTaskHandler',
        name="task-add-user",
        handler_method='get',
        strict_slash=True,
        methods=['POST'],
    ),

    ####################################
    # User facing template/form routes #
    ####################################

    Route(
        r'/',
        'handlers.user.IndexHandler',
        name="user-template-index"
    ),

    RedirectRoute(
        r'/t/',
        'handlers.user.ProjectHandler',
        name="projects",
        strict_slash=True,
    ),

    RedirectRoute(
        r'/t/<task_id>/',
        'handlers.user.ViewTaskHandler',
        name="task-view",
        strict_slash=True,
    ),

    RedirectRoute(
        r'/t/<task_id>/new/',
        'handlers.user.AddTaskHandler',
        name="task-add",
        handler_method='get',
        strict_slash=True,
        methods=['GET', 'POST'],
    ),

    RedirectRoute(
        r'/t/<task_id>/reassign/',
        'handlers.user.ReassignTaskHandler',
        name="task-reassign",
        handler_method='get',
        strict_slash=True,
        methods=['POST'],
    ),

    RedirectRoute(
        r'/t/<task_id>/completion/',
        'handlers.user.CompletionTaskHandler',
        name="task-completion",
        handler_method='get',
        strict_slash=True,
        methods=['POST'],
    ),

    RedirectRoute(
        r'/t/<task_id>/comment/',
        'handlers.user.AddCommentHandler',
        name="task-comment",
        handler_method='get',
        strict_slash=True,
        methods=['POST'],
    ),

    #############################
    # Auth/Login related routes #
    #############################

    Route(
        r'/auth_callback',
        'handlers.auth.CallbackHandler',
        name="oauth-callback"
    ),

]
