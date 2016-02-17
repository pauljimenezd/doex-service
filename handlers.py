# -*- coding: utf-8 -*-
import webapp2
import json
from models import Currency, Rate
from google.appengine.api import memcache


class Currencies(webapp2.RequestHandler):
    def get(self, code=None):
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

        # Setting response header
        self.response.content_type = 'application/json; charset=utf-8'
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
        from datetime import date
        # key = unicode(currency) + date.today().strftime('%Y%m%d')
        # rate = memcache.get(key)
        cur = Currency.get_by_id(currency.lower())
        if not cur:
            webapp2.abort(404)

        rates = Rate.query(ancestor=cur.key).order(Rate.date).fetch()

        self.response.content_type = 'application/json; charset=utf-8'
        return self.response.out.write(json.dumps(rates, cls=Rate.JSONEncoder))


class TodayRates(webapp2.RequestHandler):
    def get(self, currency=None):
        from datetime import date, timedelta
        cur = None
        if currency:
            cur = Currency.get_by_id(currency.lower())
            if not cur:
                webapp2.abort(404)

        date_param = date.today() - timedelta(days=1)

        if cur:
            result = Rate.query(Rate.currency == cur.key, Rate.date == date_param).get()
        else:
            result = Rate.query(Rate.date == date_param).fetch()

        if not result:
            webapp2.abort(404)

        self.response.content_type = 'application/json; charset=utf-8'
        resp = json.dumps(result, cls=Rate.FullJSONEncoder)
        return self.response.out.write(resp)
