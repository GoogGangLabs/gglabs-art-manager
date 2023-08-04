class BaseLogger:
    def open(self):
        pass

    def log(self, s: str):
        pass

    def close(self):
        pass


class StdoutLogger(BaseLogger):
    def log(self, s: str):
        print(s)
