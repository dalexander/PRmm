
# This isn't really "mocking", it's really more of a "stub" class

class Mock(dict):

    def __init__(self, **kwargs):
        for (k, v) in kwargs.iteritems():
            self[k] = v


    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise self.__attr_error(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise self.__attr_error(name)

    def __attr_error(self, name):
        return AttributeError("type object '{subclass_name}' has no attribute '{attr_name}'".format(subclass_name=type(self).__name__, attr_name=name))

    def copy(self):
        return adict(self)
