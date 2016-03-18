#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json

import webapp2
from webapp2_extras import routes

import handlers
import tasks


def handle_404(request, response, exception):
    # logging.exception(exception)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = 'application/json; charset=utf-8'
    response.set_status(404)


def handle_500(request, response, exception):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = 'application/json; charset=utf-8'
    response.set_status(500)
    response.out.write(json.dumps({u'code': 500, u'title': u'Internal Server Error', u'detail': u'The server has either erred or is incapable of performing the requested operation.'}))


def error_handler(request, response, exception):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = 'application/json; charset=utf-8'
    response.set_status(exception.code)
    response.out.write(json.dumps({'code': exception.code, 'title': exception.title, 'detail': str(exception.wsgi_response)}))


app = webapp2.WSGIApplication([
    webapp2.Route('/', webapp2.RedirectHandler, defaults={'_uri': 'http://pauljimenez.com.do/doex'}),
    routes.PathPrefixRoute('/api', [
        # Currencies routes
        routes.PathPrefixRoute('/currencies', [
            webapp2.Route('', handler=handlers.Currencies, name='currencies'),
            webapp2.Route(r'/<code:[a-z]{3}>', handler=handlers.Currencies, name='currency'),
            webapp2.Route(r'/<currency:[a-z]{3}>/rates', handler=handlers.Rates, name='currency-rates-list'),
            webapp2.Route(r'/<currency:[a-z]{3}>/rates/<date:[0-9]{4}-[0-9]{2}-[0-9]{2}>', handler=handlers.Rates, name='currency-rates-date'),
        ]),
        # Rates routes
        routes.PathPrefixRoute(r'/rates', [
            webapp2.Route('', handler=handlers.Rates, name='rates'),
            webapp2.Route(r'/<currency:[a-z]{3}>', handler=handlers.Rates, name='currency-rates'),
            webapp2.Route(r'/<date:[0-9]{4}-[0-9]{2}-[0-9]{2}>', handler=handlers.Rates, name='rates-date'),
            webapp2.Route(r'/<date:[0-9]{4}-[0-9]{2}-[0-9]{2}>/<currency:[a-z]{3}>', handler=handlers.Rates, name='rates-date-currency'),
            webapp2.Route(r'/<:[0-9]{4}-[0-9]{2}-[0-9]{2}>/<code:[a-z]{3}>/currency', handler=handlers.Currencies, name='rate-currency'),
        ]),
        # Tasks routes
        routes.PathPrefixRoute('/tasks', [
            routes.PathPrefixRoute('/rates', [
                webapp2.Route('/update', handler=tasks.RatesUpdateTasks, handler_method='update', name='task-rate-update'),
                # webapp2.Route('/sync', handler=tasks.RatesUpdateTasks, handler_method='synchronize', name='task-rate-sync'),
            ])
        ]),
    ]),
], debug=False)

app.error_handlers[404] = error_handler
app.error_handlers[400] = error_handler
app.error_handlers[500] = handle_500


def main():
    app.run()


if __name__ == '__main__':
    main()
