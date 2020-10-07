import abc


class Filter(abc.ABC):

    @abc.abstractmethod
    def filter(self):
        pass
