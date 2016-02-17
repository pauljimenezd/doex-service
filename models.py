# -*- coding: utf-8 -*-
from google.appengine.ext import ndb
from json import JSONEncoder

__author__ = 'pejimenezd'


class BaseJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, ndb.Query):
            return [self.default(d) for d in o]

        return self.process_encode(o)

    def process_encode(self, o):
        return super(BaseJSONEncoder, self).default(o)


class Currency(ndb.Model):
    class JSONEncoder(JSONEncoder):
        def default(self, o):
            if isinstance(o, Currency):
                return {u'code': o.key.id(), u'name': o.name}

            if isinstance(o, ndb.Query):
                return [self.default(cur) for cur in o]

            return super(Currency.JSONEncoder, self).default(o)

    name = ndb.StringProperty(required=True, indexed=False)

    @staticmethod
    def factory(data):
        if type(data) is dict:
            result = Currency(id=data['code'], name=data['name'])
        elif type(data) is list:
            result = [Currency(id=obj['code'], name=obj['name']) for obj in data]

        return result


class Rate(ndb.Model):
    class JSONEncoder(BaseJSONEncoder):
        def process_encode(self, o):
            if isinstance(o, Rate):
                return {u'date': o.date.isoformat(), u'value': o.value, u'created': o.created.isoformat()}
            return super(BaseJSONEncoder, self).process_encode(o)

    class FullJSONEncoder(BaseJSONEncoder):
        def process_encode(self, o):
            if isinstance(o, Rate):
                return {u'date': o.date.isoformat(), u'currency': o.currency.id(), u'value': o.value, u'created': o.created.isoformat()}
            return super(BaseJSONEncoder, self).process_encode(o)

    currency = ndb.KeyProperty(kind=Currency)
    date = ndb.DateProperty(required=True)
    value = ndb.FloatProperty(default=None)
    created = ndb.DateTimeProperty(auto_now_add=True)


class Config(ndb.Model):
    @property
    def name(self):
        key_value = None
        if self.key().has_id_or_name():
            key_value = self.key().name()

        return key_value

    value = ndb.StringProperty(required=True)
