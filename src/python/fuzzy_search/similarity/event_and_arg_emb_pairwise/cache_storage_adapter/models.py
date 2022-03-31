import abc
import typing

class CacheStorageAdapter(abc.ABC):

    @abc.abstractmethod
    def store(self,feature):
        pass

    @abc.abstractmethod
    def query_by_vector(self,vector,feature_name,topK,**kwargs):
        pass

    @abc.abstractmethod
    def init_storage(self,**kwargs):
        pass

    @abc.abstractmethod
    def finalize_storage(self,**kwargs):
        pass

    @staticmethod
    def load_storage(**kwargs):
        pass