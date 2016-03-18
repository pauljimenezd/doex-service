# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta, date
import re

from google.appengine.ext import ndb
import webapp2
from google.appengine.api import memcache

from models import Currency, Rate
from utils import AtlanticTimezone, etag, jsonresponse, allow_origin, cache


class Currencies(webapp2.RequestHandler):
    @etag
    @jsonresponse
    @cache(age=timedelta(days=6).total_seconds())
    @allow_origin('*')
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
            webapp2.abort(204)

        self.response.out.write(json.dumps(result, cls=Currency.JSONEncoder))


    @staticmethod
    def __get_single(code):
        cache_key = 'currency-' + code
        currency = memcache.get(key=cache_key)
        if not currency:
            currency = Currency.get_by_id(id=code)
            memcache.set(key=cache_key, value=json.dumps(currency, cls=Currency.JSONEncoder), time=3600)
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
    @etag
    @jsonresponse
    @cache(age=timedelta(hours=6).total_seconds())
    @allow_origin('*')
    def get(self, date=None, currency=None):
        """
        Handler for the GET requests
        :param currency:
        :return:
        """

        filter_arg = self.request.get('filter', 'today')
        filter_days_pattern = r'([0-9]+)d'
        filter_date_pattern = r'([0-9]{4}-[0-9]{2}-[0-9]{2})'

        if currency and not Currency.get_by_id(id=currency):
            webapp2.abort(404)

        filter_dates = None, None
        if date is None:
            if filter_arg == 'today':
                filter_dates = Rates.Filters.today()

            elif filter_arg == 'this-month':
                filter_dates = Rates.Filters.this_month()

            elif filter_arg == 'this-week':
                filter_dates = Rates.Filters.this_week()

            elif filter_arg == 'all':
                filter_dates = None, None

            elif filter_arg == 'yesterday':
                filter_dates = Rates.Filters.yesterday()

            elif filter_arg == 'last-week':
                filter_dates = Rates.Filters.last_week(currency=currency)

            elif filter_arg == 'last-month':
                filter_dates = Rates.Filters.last_month()

            elif re.match(filter_days_pattern, filter_arg):
                groups = re.match(filter_days_pattern, filter_arg).groups()
                filter_dates = Rates.Filters.by_days(days=int(groups[0]))

            elif re.match(filter_date_pattern, filter_arg):
                groups = re.match(filter_date_pattern, filter_arg).groups()
                filter_dates = Rates.Filters.date(date_filtering=groups[0])

            else:
                webapp2.abort(400)
        else:
            try:
                filter_dates = datetime.strptime(date, '%Y-%m-%d').date(), None
            except ValueError:
                webapp2.abort(400)

        mem_key = Rates.get_mkey(start=filter_dates[0], end=filter_dates[1], currency=currency)

        if filter_dates[0] and filter_dates[1]:
            result = Rates.get_range(memkey=mem_key, start=filter_dates[0], end=filter_dates[1], currency=currency)
        elif filter_dates[0]:
            result = Rates.get_single(memkey=mem_key, date=filter_dates[0], currency=currency)
        else:
            result = Rates.get_all(memkey=mem_key, currency=currency)

        if not result:
            webapp2.abort(204)

        response = json.dumps(result, cls=Rate.FullJSONEncoder) if type(result) not in (str, unicode) else result
        self.response.out.write(response)

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
    def get_all(memkey, currency=None):
        """
        Retrieve all rate for the current month.
        :param currency: str
        :return: object
        """
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
    def get_single(memkey, date, currency=None):
        """
        Retrieve single date from the datastore of the selected date and currency.
        :param currency:
        :param date:
        :return:
        """
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
    def get_range(memkey, start, end, currency):
        """
        Retrieve range of rates from datastore of the selected dates and currency.
        :param currency:
        :param start:
        :param end:
        :return:
        """
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

    @staticmethod
    def get_mkey(start=None, end=None, currency=None):
        # Generating the data key for the cache
        memkey = "RATE%(begin)s%(end)s%(suf)s" % {
            'begin': (start.toordinal() if type(start) in (datetime, date) else (start or '')),
            'end': (end.toordinal() if type(end) in (datetime, date) else (end or '')),
            'suf': (currency or '').upper()
        }
        return memkey.strip()

    class Filters:
        @staticmethod
        def get_closing_date(filter_date):
            # Setting the date for the previous closing date.
            filter_date -= timedelta(days=1)

            # Verify if the date is weekend. Select the previews friday.
            if filter_date.weekday() in (5, 6):
                filter_date -= timedelta(days=filter_date.weekday() - 4)

            if filter_date.month == 12 and filter_date.day == 25:
                filter_date -= timedelta(days=1)

            return filter_date

        @staticmethod
        def today():
            """
            Retrieve the rate for active for today
            :return: list
            """
            today = datetime.now(AtlanticTimezone()).date()
            start = Rates.Filters.get_closing_date(today)

            return start, None

        @staticmethod
        def this_month():
            """
            Retrieve all rate for the current month.
            :return: object
            """
            # Selecting the date for filtering results for the rate active for the current day.
            end = datetime.now(AtlanticTimezone()).date()
            if end.day is not 1:
                start = end.replace(day=1)
            else:
                start = end

            start = Rates.Filters.get_closing_date(start)
            end = Rates.Filters.get_closing_date(end)

            return start, end

        @staticmethod
        def this_week():
            """
            Retrieve all rate for the current month.
            :return:
            """
            # Selecting the date for filtering results for the rate active for the current day.
            end = datetime.now(AtlanticTimezone()).date()
            if end.weekday() is not 0:
                start = end - timedelta(days=end.weekday())
            else:
                start = end

            start = Rates.Filters.get_closing_date(start)
            end = Rates.Filters.get_closing_date(end)

            return start, end

        @staticmethod
        def by_days(days):
            """
            Retrieve an amount of days form the datastore
            :type currency: str
            :param days: int
            :param currency: str
            :return: object
            """
            # Selecting the date for filtering results for the rate active for the current day.
            end = datetime.now(AtlanticTimezone()).date()  # Getting the active date for the -4:00 region

            start = end - timedelta(days=days)

            start = Rates.Filters.get_closing_date(start)
            end = Rates.Filters.get_closing_date(end)

            return start, end

        @staticmethod
        def date(date_filtering):
            """
            Filter rate active for the given date_filtering.
            :param date_filtering:
            String of the given date_filtering in iso_format.
            :param currency:
            String of the selected currency in iso_code.
            :return:
            """
            try:
                date_filtering = datetime.strptime(date_filtering, '%Y-%m-%d').date()
            except ValueError:
                webapp2.abort(400)

            start = Rates.Filters.get_closing_date(date_filtering)

            return start, None

        @staticmethod
        def yesterday():
            """

            :return:
            """
            search_date = datetime.now(AtlanticTimezone()).date()

            # Selecting the date for filtering results for the rate active for the current day.
            search_date -= timedelta(days=1)  # Getting the active date for the -4:00 region

            search_date = Rates.Filters.get_closing_date(search_date)

            return search_date, None

        @staticmethod
        def last_week(currency=None):
            """

            :type currency: str
            :param currency:
            :return:
            """
            # Selecting the date for filtering results for the rate active for the current day.
            today = datetime.now(AtlanticTimezone()).date()

            if today.weekday() is not 0:
                start = today - timedelta(days=today.weekday())
            else:
                start = today

            start -= timedelta(weeks=1)
            end = start + timedelta(days=6)

            start = Rates.Filters.get_closing_date(start)
            end = Rates.Filters.get_closing_date(end)

            return start, end

        @staticmethod
        def last_month():
            """

            :return:
            """
            # Selecting the date for filtering results for the rate active for the current day.
            today = datetime.now(AtlanticTimezone()).date()
            if today.day is not 1:
                start = today.replace(day=1)
            else:
                start = today

            end = start - timedelta(days=1)
            start = start.replace(month=start.month - 1)

            start = Rates.Filters.get_closing_date(start)
            end = Rates.Filters.get_closing_date(end)

            return start, end
