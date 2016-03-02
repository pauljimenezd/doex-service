# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
import re

from google.appengine.ext import ndb
import webapp2

from google.appengine.api import memcache

from models import Currency, Rate
from utils import AtlanticTimezone


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
            webapp2.abort(204)

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
    def get(self, date=None, currency=None):
        """
        Handler for the GET requests
        :param currency:
        :return:
        """
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.content_type = 'application/json; charset=utf-8'

        filter_arg = self.request.get('f', 'today')
        filter_days_pattern = r'([0-9]+)d'
        filter_date_pattern = r'([0-9]{4}-[0-9]{2}-[0-9]{2})'

        if currency and not Currency.get_by_id(id=currency):
            webapp2.abort(404)

        result = None
        if date is None:
            if filter_arg == 'today':
                result = Rates.Filters.today(currency=currency)
            elif filter_arg == 'now':
                result = Rates.Filters.now(currency=currency)
            elif filter_arg == 'this-month':
                result = Rates.Filters.this_month(currency=currency)
            elif filter_arg == 'this-week':
                result = Rates.Filters.this_week(currency=currency)
            elif filter_arg == 'all':
                result = Rates.get_all(currency=currency)
            elif filter_arg == 'yesterday':
                result = Rates.Filters.yesterday(currency=currency)
            elif filter_arg == 'last-week':
                result = Rates.Filters.last_week(currency=currency)
            elif filter_arg == 'last-month':
                result = Rates.Filters.last_month(currency=currency)
            elif re.match(filter_days_pattern, filter_arg):
                groups = re.match(filter_days_pattern, filter_arg).groups()
                result = Rates.Filters.by_days(days=int(groups[0]), currency=currency)
            elif re.match(filter_date_pattern, filter_arg):
                groups = re.match(filter_date_pattern, filter_arg).groups()
                result = Rates.Filters.date(date=groups[0], currency=currency)
            else:
                webapp2.abort(400)
        else:
            try:
                date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                webapp2.abort(404)

            result = Rates.get_single(currency=currency, date=date)

        if not result:
            webapp2.abort(204)

        response = json.dumps(result, cls=Rate.FullJSONEncoder) if type(result) not in (str, unicode) else result
        return self.response.out.write(response)

    @staticmethod
    def cache(memkey, result):
        """
        Save the result in the cache with the default timing
        :param memkey: str
        :param result: object
        :return:
        """
        # Caching rate data
        memcache.add(key=memkey, value=unicode(json.dumps(result, cls=Rate.FullJSONEncoder)), time=3600)

    @staticmethod
    def get_all(currency=None):
        """
        Retrieve all rate for the current month.
        :param currency: str
        :return: object
        """
        # Generating the data key for the cache
        memkey = 'RATEA%s' % (currency or '').upper()

        # Retrieving the rate of the currency from the cache
        result = memcache.get(memkey)
        # Verify if the rate exists, if not will call the datastore.
        if not result:
            if currency:
                # Retrieving rate data form datastore for the selected currency
                result = Rate.query(Rate.currency == ndb.Key('Currency', currency.lower())).fetch()
            else:
                # Retrieving rate data form datastore for all currencies
                result = Rate.query().fetch()

            if result:
                Rates.cache(memkey, result)
        return result

    @staticmethod
    def get_single(currency, date):
        """
        Retrieve single date from the datastore of the selected date and currency.
        :param currency:
        :param date:
        :return:
        """
        # Generating the data key for the cache
        memkey = "RATE%(id)d%(suf)s" % {'id': date.toordinal(), 'suf': (currency or '').upper()}
        # Retrieving the rate of the currency from the cache
        result = memcache.get(memkey)
        # Verify if the rate exists, if not will call the datastore.
        if not result:
            if currency:
                # Retrieving rate data form datastore for the selected currency
                result = Rate.query(Rate.currency == ndb.Key('Currency', currency.lower()), Rate.date == date).get()
            else:
                # Retrieving rate data form datastore for all currencies
                result = Rate.query(Rate.date == date).fetch()

            if result:
                Rates.cache(memkey, result)
        return result

    @staticmethod
    def get_range(currency, start, end):
        """
        Retrieve range of rates from datastore of the selected dates and currency.
        :param currency:
        :param start:
        :param end:
        :return:
        """
        # Generating the data key for the cache
        memkey = "RATE%(begin)d%(end)d%(suf)s" % {'begin': start.toordinal(), 'end': end.toordinal(), 'suf': (currency or '').upper()}

        # Retrieving the rate of the currency from the cache
        result = memcache.get(memkey)
        # Verify if the rate exists, if not will call the datastore.
        if not result:
            if currency:
                # Retrieving rate data form datastore for the selected currency
                result = Rate.query(Rate.currency == ndb.Key('Currency', currency.lower()), ndb.AND(Rate.date >= start, Rate.date <= end)).fetch()
            else:
                # Retrieving rate data form datastore for all currencies
                result = Rate.query(ndb.AND(Rate.date >= start, Rate.date <= end)).fetch()

            if result:
                Rates.cache(memkey, result)
        return result

    class Filters:
        @staticmethod
        def today(currency=None):
            """
            Retrieve the rate for active for today
            :param currency: str
            :return: list
            """
            today = datetime.now(AtlanticTimezone()).date()

            # Selecting the date for filtering results for the rate active for the current day.
            today -= timedelta(days=1)  # Getting the active date for the -4:00 region

            # Verify if the date is weekend. Select the previews friday.
            if today.weekday() in (5, 6):
                today -= timedelta(days=today.weekday() - 4)

            result = Rates.get_single(currency=currency, date=today)
            return result

        @staticmethod
        def now(currency):
            """
            Retrieve the last or actual rate.
            :param currency: str
            :return: object
            """
            date = datetime.now(AtlanticTimezone()).date()

            # Verify if the date is weekend. Select the previews friday.
            if date.weekday() in (5, 6):
                date -= timedelta(days=date.weekday() - 4)

            result = Rates.get_single(currency=currency, date=date)

            if not result:
                date -= timedelta(days=1)

                # Verify if the date is weekend. Select the previews friday.
                if date.weekday() in (5, 6):
                    date -= timedelta(days=date.weekday() - 4)

                result = Rates.get_single(currency=currency, date=date)
            return result

        @staticmethod
        def this_month(currency=None):
            """
            Retrieve all rate for the current month.
            :param currency: str
            :return: object
            """
            # Selecting the date for filtering results for the rate active for the current day.
            end = datetime.now(AtlanticTimezone()).date()
            if end.day is not 1:
                start = end.replace(day=1)
                end -= timedelta(days=1)
            else:
                start = end

            # Verification if the weekday is sunday or monday
            if start.weekday() in (0, 1):
                start -= timedelta(days=start.weekday() + 1)

            # Verify if the date is weekend. Select the previews friday.
            if start.weekday() in (5, 6):
                start -= timedelta(days=start.weekday() - 4)

            # Verify if the date is weekend. Select the previews friday.
            if end.weekday() in (5, 6):
                end -= timedelta(days=end.weekday() - 4)

            result = Rates.get_range(currency=currency, start=start, end=end)
            return result

        @staticmethod
        def this_week(currency=None):
            """
            Retrieve all rate for the current month.
            :param currency: str
            :return: object
            """
            # Selecting the date for filtering results for the rate active for the current day.
            end = datetime.now(AtlanticTimezone()).date()
            if end.weekday() is not 0:
                start = end - timedelta(days=end.weekday())
                end -= timedelta(days=1)
            else:
                start = end

            result = Rates.get_range(currency=currency, start=start, end=end)
            return result

        @staticmethod
        def by_days(days, currency=None):
            """
            Retrieve an amount of days form the datastore
            :type currency: str
            :param days: int
            :param currency: str
            :return: object
            """
            # Selecting the date for filtering results for the rate active for the current day.
            end = datetime.now(AtlanticTimezone()).date() - timedelta(days=1)  # Getting the active date for the -4:00 region

            # Verify if the date is weekend. Select the previews friday.
            if end.weekday() in (5, 6):
                end = end - timedelta(days=end.weekday() - 4)

            start = end - timedelta(days=days)

            result = Rates.get_range(currency=currency, start=start, end=end)
            return result

        @staticmethod
        def date(date, currency=None):
            """
            Filter rate active for the given date.
            :param date:
            String of the given date in iso_format.
            :param currency:
            String of the selected currency in iso_code.
            :return:
            """
            try:
                date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                webapp2.abort(400)

            # Selecting the date for filtering results for the rate active for the current day.
            date -= timedelta(days=1)  # Getting the active date for the -4:00 region

            # Verify if the date is weekend. Select the previews friday.
            if date.weekday() in (5, 6):
                date -= timedelta(days=date.weekday() - 4)

            result = Rates.get_single(currency, date)

            return result

        @staticmethod
        def yesterday(currency=None):
            """

            :type currency: str
            :param currency:
            :return:
            """
            today = datetime.now(AtlanticTimezone()).date()

            # Selecting the date for filtering results for the rate active for the current day.
            today -= timedelta(days=2)  # Getting the active date for the -4:00 region

            # Verify if the date is weekend. Select the previews friday.
            if today.weekday() in (5, 6):
                today -= timedelta(days=today.weekday() - 4)

            result = Rates.get_single(currency=currency, date=today)
            return result

        @staticmethod
        def last_week(currency=None):
            """

            :type currency: str
            :param currency:
            :return:
            """
            # Selecting the date for filtering results for the rate active for the current day.
            end = datetime.now(AtlanticTimezone()).date()

            if end.weekday() is not 0:
                start = end - timedelta(days=end.weekday())
                end -= timedelta(days=1)
            else:
                start = end

            start -= timedelta(weeks=1)
            end -= timedelta(weeks=1)

            result = Rates.get_range(currency=currency, start=start, end=end)
            return result

        @staticmethod
        def last_month(currency=None):
            """

            :type currency: str
            :param currency:
            :return:
            """
            # Selecting the date for filtering results for the rate active for the current day.
            end = datetime.now(AtlanticTimezone()).date()
            if end.day is not 1:
                start = end.replace(day=1)
                end -= timedelta(days=1)
            else:
                start = end

            end = start - timedelta(days=1)
            start = start.replace(month=start.month - 1)

            # Verification if the weekday is sunday or monday
            if start.weekday() in (0, 1):
                start -= timedelta(days=start.weekday() + 1)

            # Verify if the date is weekend. Select the previews friday.
            if start.weekday() in (5, 6):
                start -= timedelta(days=start.weekday() - 4)

            # Verify if the date is weekend. Select the previews friday.
            if end.weekday() in (5, 6):
                end -= timedelta(days=end.weekday() - 4)

            result = Rates.get_range(currency=currency, start=start, end=end)
            return result
