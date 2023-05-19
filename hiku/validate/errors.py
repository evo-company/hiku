from typing import List


class Errors:
    def __init__(self) -> None:
        self.list: List[str] = []

    def report(self, msg: str) -> None:
        self.list.append(msg)
