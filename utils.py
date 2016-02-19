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
