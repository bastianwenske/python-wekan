class WekanBase(object):
    def __init__(self) -> None:
        self.id = None

    def __hash__(self) -> int:
        class_name = type(self).__name__
        return hash(class_name) ^ hash(self.id)

    def __eq__(self, other) -> hash:
        if isinstance(other, type(self)):
            return hash(self) == hash(other)
        else:
            raise NotImplementedError
