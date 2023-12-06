from cgg.apps.finance.models import CommandRun


def log_command(command_title):
    """
    log running command
    :param command_title: choices from CommandRun model
    :return:
    """

    def wrapper(view_method):
        def args_wrapper(class_view_obj, *args, **kwargs):
            view_result = view_method(class_view_obj, *args, **kwargs)
            command_run = CommandRun()
            command_run.command_title = command_title
            command_run.save()

            return view_result

        return args_wrapper

    return wrapper
