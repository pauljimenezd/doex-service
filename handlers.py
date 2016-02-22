# -*- coding: utf-8 -*-
import json

from google.appengine.ext import ndb
import webapp2
from google.appengine.api import memcache

from models import Currency, Rate


class Currencies(webapp2.RequestHandler):
    def get(self, code=None):
        # Setting response header
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.content_type = 'application/json; charset=utf-8'

        # Verification for retrieve only one record or list
        if code is not None:
            # Retrieving single record
            result = self.__get_single(code)
        else:
            # Retrieving all of the records
            result = self.__get_all()

        if result is None:
            # Return a 404 if no record was found
            webapp2.abort(404)

        return self.response.out.write(json.dumps(result, cls=Currency.JSONEncoder))

    def post(self):
        auth_key = self.request.headers.get('key', None)
        if not auth_key:
            webapp2.abort(404)

    @staticmethod
    def __get_single(code):
        cache_key = 'currency-' + code
        currency = memcache.get(key=cache_key)
        if not currency:
            currency = Currency.get_by_id(id=code)
            memcache.add(key=cache_key, value=json.dumps(currency, cls=Currency.JSONEncoder), time=3600)
        else:
            obj = json.loads(currency)
            currency = Currency.factory(obj)

        return currency

    @staticmethod
    def __get_all():
        key = 'currencies-list'
        # Retrieving data from memcache
        currency_list = memcache.get(key=key)

        if not currency_list:
            # Retrieving list from the datastore due to not found on cache
            currency_list = Currency.query().fetch()
            # Saving the result to the cache for 1hr
            memcache.add(key=key, value=json.dumps(currency_list, cls=Currency.JSONEncoder), time=3600)
        else:
            obj_list = json.loads(currency_list)
            currency_list = Currency.factory(obj_list)

        return currency_list


class Rates(webapp2.RequestHandler):
    def get(self, currency):
        # Setting response header
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.content_type = 'application/json; charset=utf-8'

        rates = Rate.query(Rate.currency == ndb.Key('Currency', currency.lower())).order(-Rate.date).fetch(60)

        return self.response.out.write(json.dumps(rates, cls=Rate.JSONEncoder))

    def today(self, currency=None):
        from utils import AtlanticTimezone
        from datetime import datetime, timedelta
        # Setting response header
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.content_type = 'application/json; charset=utf-8'

        date_param = datetime.now(AtlanticTimezone()).date() - timedelta(days=1)
        if date_param.weekday() in (5, 6):
            date_param = date_param - timedelta(days=date_param.weekday() - 4)

        if currency:
            result = Rate.query(Rate.currency == ndb.Key('Currency', currency.lower()), Rate.date == date_param).get()
            if not result:
                webapp2.abort(404, '')
        else:
            result = Rate.query(Rate.date == date_param).fetch()

            if not result:
                webapp2.abort(404, '')

        resp = json.dumps(result, cls=Rate.FullJSONEncoder)
        return self.response.out.write(resp)

    def now(self, currency=None):
        from utils import AtlanticTimezone
        from datetime import datetime, timedelta
        # Setting response header
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.content_type = 'application/json; charset=utf-8'

        now_date = datetime.now(AtlanticTimezone()).date()
        today_date = now_date - timedelta(days=1)

        if currency:
            query = Rate.query(Rate.currency == ndb.Key('Currency', currency.lower()), ndb.OR(Rate.date == now_date, Rate.date == today_date))
            result = query.filter(Rate.date == now_date)
            if not result.count():
                result = query.filter(Rate.date == today_date)

            if not result.count():
                webapp2.abort(404, '')

            result = result.get()
        else:
            query = Rate.query(ndb.OR(Rate.date == now_date, Rate.date == today_date))
            result = query.filter(Rate.date == now_date)
            if not result.count():
                result = query.filter(Rate.date == today_date)

            if not result.count():
                webapp2.abort(404, '')

        resp = json.dumps(result, cls=Rate.FullJSONEncoder)
        return self.response.out.write(resp)

    def this_month(self, currency=None):
        from utils import AtlanticTimezone as AstZone
        from datetime import datetime, timedelta

        # Setting response header
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.content_type = 'application/json; charset=utf-8'

        _date = datetime.now(AstZone()).date()
        _date = _date.replace(day=1)

        if currency:
            results = Rate.query(Rate.currency == ndb.Key('Currency', currency), Rate.date >= _date)
        else:
            results = Rate.query(Rate.date >= _date)

        if not results.count():
            webapp2.abort(404)

        resp = json.dumps(results, cls=Rate.FullJSONEncoder)
        return self.response.out.write(resp)
