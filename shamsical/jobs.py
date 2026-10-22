"""Network work never touches widgets outside the Qt main thread."""

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal


class Signals(QObject):
    finished = pyqtSignal(int, object, str)


class Job(QRunnable):
    def __init__(self, token, function):
        super().__init__()
        self.token, self.function = token, function
        self.signals = Signals()

    def run(self):
        try:
            value, error = self.function(), ""
        except Exception:
            # Never expose URLs, tokens, response bodies, or provider exception text.
            value, error = None, "request_failed"
        self.signals.finished.emit(self.token, value, error)


class Jobs(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(3)
        self.serial = 0
        self.pending = {}

    def submit(self, function, callback):
        self.serial += 1
        job = Job(self.serial, function)
        self.pending[self.serial] = (job, callback)
        job.signals.finished.connect(self.complete)
        self.pool.start(job)
        return self.serial

    def complete(self, token, value, error):
        pending = self.pending.pop(token, None)
        if pending:
            pending[1](value, error)
