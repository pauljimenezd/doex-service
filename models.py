# -*- coding: utf-8 -*-
from google.appengine.ext import db
from json import JSONEncoder

__author__ = 'pejimenezd'


class Currency(db.Model):
    class JSONEncoder(JSONEncoder):
        def default(self, o):
            if isinstance(o, Currency):
                return {u'code': o.key().id_or_name(), u'name': o.name}

            if isinstance(o, db.Query):
                return [self.default(cur) for cur in o]

            return super(Currency.JSONEncoder, self).default(o)

    name = db.StringProperty(required=True, indexed=False)

    @staticmethod
    def factory(data):
        if type(data) is dict:
            result = Currency(key_name=data['code'], name=data['name'])
        elif type(data) is list:
            result = [Currency(key_name=obj['code'], name=obj['name']) for obj in data]

        return result


class Rate(db.Model):
    class JSONEncoder(JSONEncoder):
        def default(self, o):
            if isinstance(o, Rate):
                return {u'id': o.key().id_or_name(), u'date': o.date.isoformat(), u'value': o.value}

            if isinstance(o, db.Query):
                return [self.default(cur) for cur in o]

            return super(Rate.JSONEncoder, self).default(o)

    date = db.DateProperty(required=True)
    value = db.FloatProperty(default=None)
    created = db.DateTimeProperty(auto_now_add=True)
