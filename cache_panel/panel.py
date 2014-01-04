import cPickle as pickle
from datetime import datetime
import functools
import logging
import os.path
import pprint
import threading

from django.core import cache
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from debug_toolbar.panels import DebugPanel
from debug_toolbar.utils import get_stack, tidy_stacktrace


logger = logging.getLogger(__name__)


class Calls:

    def __init__(self):
        self.reset()

    def reset(self):
        self._calls = []

    def append(self, call):
        self._calls.append(call)

    def calls(self):
        return self._calls

    def size(self):
        return len(self._calls)

    def last(self):
        return self._calls[-1]


instance = threading.local()


def _get_calls():
    if not hasattr(instance, 'calls'):
        instance.calls = Calls()
    return instance.calls


def repr_value(ret):
    try:
        if isinstance(ret, dict):
            out = ret.copy()
            pickle_ = out.pop('__pickle__', None)
            if pickle_:
                out.update(pickle.loads(pickle_))

        elif isinstance(ret, (list, tuple)) and len(ret) == 1:
            out, = ret
        else:
            out = ret
    except Exception, e:
        try:
            out = 'Unable to parse: %r because: %r' % (ret, e)
        except:
            out = 'Unable to parse'

    out = pprint.pformat(out, indent=False, width=50)
    out = ' '.join(out.split())

    if out[100:]:
        return out[:97] + '...'
    else:
        return out[:100]


def render_stacktrace(trace):
    stacktrace = []
    for frame in trace:
        params = map(escape, frame[0].rsplit(os.path.sep, 1) + list(frame[1:]))
        try:
            stacktrace.append(u'<span class="path">{0}/</span><span class="file">{1}</span> in <span class="func">{3}</span>(<span class="lineno">{2}</span>)\n  <span class="code">{4}</span>'.format(*params))
        except IndexError:
            # This frame doesn't have the expected format, so skip it and move on to the next one
            continue
    return mark_safe('\n'.join(stacktrace))


def record(func):
    @functools.wraps(func)
    def wrapper(self, key, *args, **kwargs):
        stacktrace = tidy_stacktrace(reversed(get_stack()[1:]))
        call = {
            'function': func.__name__,
            'args': repr_value(args),
            'stacktrace': render_stacktrace(stacktrace)
        }
        _get_calls().append(call)

        if isinstance(key, dict):
            call['key'] = key.keys()
        else:
            call['key'] = key

        value = None
        try:
            # the clock starts now
            call['start'] = datetime.now()
            value = func(self, key, *args, **kwargs)
        finally:
            # the clock stops now
            dur = datetime.now() - call['start']
            call['duration'] = ((dur.seconds * 1000)
                + (dur.microseconds / 1000.0))
            if func.__name__.startswith('get'):
                default = kwargs.get('default')
                if value is None or value == default:
                    call['miss'] = 1
                else:
                    call['hit'] = 1

        call['value'] = repr_value(value)
        return value
    return wrapper


class CacheDebugPanel(DebugPanel):
    name = 'Cache'
    has_content = True
    template = 'cache_panel/cache.html'

    def process_request(self, request):
        _get_calls().reset()

    def process_response(self, request, response):
        calls = _get_calls().calls()
        stats = {'calls': 0, 'duration': 0, 'hits': 0, 'misses': 0}
        commands = {}

        for call in calls:
            stats['calls'] += 1
            stats['duration'] += call['duration']
            stats['hits'] += call.get('hit', 0)
            stats['misses'] += call.get('miss', 0)
            function = call['function']

            # defaultdict would have been nice, but it kills the django
            # templates system
            commands[function] = commands.get(function, 0) + 1

        calls = sorted(calls, key=lambda c: -c['duration'])

        if stats['misses'] and stats['hits']:
            stats['hitratio'] = 100. / stats['hits'] / stats['misses']
        elif stats['hits']:
            stats['hitratio'] = 100.
        else:
            stats['hitratio'] = 0

        self.record_stats({
            'calls': calls,
            'stats': stats,
            'commands': commands,
        })

    def nav_title(self):
        return _('Cache')

    def nav_subtitle(self):
        duration = 0
        calls = _get_calls().calls()
        for call in calls:
            duration += call['duration']
        n = len(calls)
        if (n > 0):
            return '%d calls, %0.2fms' % (n, duration)
        else:
            return '0 calls'

    def title(self):
        return _('Cache Calls')

    def url(self):
        return ''


class CacheWrapper(object):
    """
    Hijacks several methods from the cache backend and logs calls.
    Modified from https://github.com/jbalogh/django-debug-cache-panel
    """

    def __init__(self, cache):
        # These are the methods we're going to replace.
        methods = ['add', 'get', 'set', 'delete', 'get_many', 'set_many',
                   'delete_many', 'incr', 'decr', 'has_key', 'clear']

        # Define fallback function if backend doesn't implement some method.
        def not_implemented(*args, **kwargs):
            raise NotImplementedError, "No such method in backend"

        # Store copies of the true methods.
        self.real_methods = dict(
            (m, getattr(cache, m, not_implemented)) for m in methods)

        # Hijack the cache object.
        for method in methods:
            setattr(cache, method, getattr(self, method))

    @record
    def add(self, *args, **kwargs):
        return self.real_methods['add'](*args, **kwargs)

    @record
    def get(self, *args, **kwargs):
        return self.real_methods['get'](*args, **kwargs)

    @record
    def set(self, *args, **kwargs):
        return self.real_methods['set'](*args, **kwargs)

    @record
    def delete(self, *args, **kwargs):
        return self.real_methods['delete'](*args, **kwargs)

    @record
    def get_many(self, *args, **kwargs):
        return self.real_methods['get_many'](*args, **kwargs)

    @record
    def set_many(self, *args, **kwargs):
        return self.real_methods['set_many'](*args, **kwargs)

    @record
    def delete_many(self, *args, **kwargs):
        return self.real_methods['delete_many'](*args, **kwargs)

    @record
    def incr(self, *args, **kwargs):
        return self.real_methods['incr'](*args, **kwargs)

    @record
    def decr(self, *args, **kwargs):
        return self.real_methods['decr'](*args, **kwargs)

    @record
    def has_key(self, *args, **kwargs):
        return self.real_methods['has_key'](*args, **kwargs)

    def clear(self):
        return self.real_methods['clear']()


if not isinstance(cache.cache, CacheWrapper):
    wrapper = CacheWrapper(cache.cache)
    cache.cache = wrapper
