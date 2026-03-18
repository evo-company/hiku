class Errors:
    def __init__(self) -> None:
        self.list: list[str] = []

    def report(self, msg: str) -> None:
        self.list.append(msg)
