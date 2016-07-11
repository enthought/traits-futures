import traceback

# Job runner messages.

STARTING = "Starting"
RAISED = "Raised"
RETURNED = "Returned"
INTERRUPTED = "Interrupted"


class JobRunner(object):
    """
    Wrapper around the actual callable to be run. This wrapper
    provides the callable that the concurrent.futures executor
    will use.
    """
    def __init__(self, job, job_id, results_queue):
        self.job_id = job_id
        self.results_queue = results_queue
        self.job = job

    def __call__(self):
        self.send(STARTING)
        try:
            result = self.job()
        except BaseException as e:
            marshalled_exception = traceback.format_exc(e)
            self.send(RAISED, marshalled_exception)
        else:
            self.send(RETURNED, result)

    def send(self, message_type, message_args=None):
        self.results_queue.put((self.job_id, message_type, message_args))
