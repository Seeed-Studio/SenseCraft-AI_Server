from threading import Condition


class StreamingOutput(object):
    def __init__(self):
        self.results = None
        self.orig_img = None
        self.condition = Condition()

    def write(self, result, orig_img=None):
        with self.condition:
            self.results = result
            self.orig_img = orig_img
            self.condition.notify_all()
