# -*- coding: utf-8 -*-
from datetime import tzinfo, timedelta
import time as _time


class AtlanticTimezone(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-4)

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return _time.tzname[AtlanticTimezone._isdst(dt)]

    @staticmethod
    def _isdst(dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = _time.mktime(tt)
        tt = _time.localtime(stamp)
        return tt.tm_isdst > 0


def jsonresponse(view_method):
    def wrapper(*args, **kwargs):
        args[0].response.content_type = 'application/json'
        view_method(*args, **kwargs)

    return wrapper


def etag(view_method):
    def wrapper(handler, *args, **kwargs):
        from hashlib import sha1
        from google.appengine.api import memcache
        import webapp2

        tagkey = 'TAG' + sha1(handler.request.path_qs).hexdigest()[:7]
        # comparing etag
        if handler.request.if_none_match:
            tag = memcache.get(tagkey)
            if tag and tag in handler.request.if_none_match:
                handler.response.etag = tag
                webapp2.abort(304)

        view_method(handler, *args, **kwargs)
        handler.response.md5_etag()
        memcache.set(key=tagkey, value=handler.response.etag, time=timedelta(hours=4).total_seconds())

    return wrapper


def cache(age):
    def set_cache(view_method):
        def wrapper(handler, *args, **kwargs):
            handler.response.cache_control = 'public, max-age=%d' % age
            view_method(handler, *args, **kwargs)

        return wrapper

    return set_cache


def allow_origin(origin):
    def set_allow_control(view_method):
        def wrapper(handler, *args, **kwargs):
            handler.response.headers['Access-Control-Allow-Origin'] = origin
            view_method(handler, *args, **kwargs)

        return wrapper

    return set_allow_control
