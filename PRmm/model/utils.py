from functools import wraps


def cached(f):
    """
    Decorator that lets us memoize the return value of a nullary
    function call in an object-local cache.
    """
    @wraps(f)
    def g(self):
        if not hasattr(self, "_cache"):
            self._cache = {}
        if f.__name__ not in self._cache:
            self._cache[f.__name__] = f(self)
        else:
            #print "Cache hit!"
            pass
        return self._cache[f.__name__]
    return g
