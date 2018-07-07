import traceback


def marshal_exception(e):
    """
    Turn exception details into something that can be safely
    transmitted across thread / process boundaries.
    """
    exc_type = str(type(e))
    exc_value = str(e)
    formatted_traceback = traceback.format_exc()
    return exc_type, exc_value, formatted_traceback
