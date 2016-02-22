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
import webapp2
import handlers
import tasks


def handle_404(request, response, exception):
    # logging.exception(exception)
    # response.write('Oops! I could swear this page was here!')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = 'application/json; charset=utf-8'
    response.set_status(404)


def handle_500(request, response, exception):
    # response.write('A server error occurred!')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.content_type = 'application/json; charset=utf-8'
    response.set_status(webapp2.exc.HTTPServerError)


app = webapp2.WSGIApplication([
    webapp2.Route(r'/currencies', handler=handlers.Currencies, name='currency'),
    webapp2.Route(r'/currencies/<code:[a-z]{3}>', handler=handlers.Currencies, name='currencies-list'),
    webapp2.Route(r'/currencies/<currency:[a-z]{3}>/rates', handler=handlers.Rates, name='currency-rates-list'),
    # Rates route
    webapp2.Route(r'/rates', handler=handlers.Rates, handler_method='today', name='rates-today'),
    webapp2.Route(r'/rates/today', handler=handlers.Rates, handler_method='today', name='rates-today'),
    webapp2.Route(r'/rates/now', handler=handlers.Rates, handler_method='now', name='rates-now'),
    webapp2.Route(r'/rates/this-month', handler=handlers.Rates, handler_method='this_month', name='rates-this-mont'),
    webapp2.Route(r'/rates/<currency:[a-z]{3}>', handler=handlers.Rates, handler_method='today', name='rates-today-currency'),
    webapp2.Route(r'/rates/<currency:[a-z]{3}>/today', handler=handlers.Rates, handler_method='today', name='rates-today-currency'),
    webapp2.Route(r'/rates/<currency:[a-z]{3}>/now', handler=handlers.Rates, handler_method='now', name='rates-now'),
    webapp2.Route(r'/rates/<currency:[a-z]{3}>/this-month', handler=handlers.Rates, handler_method='this_month', name='rates-this-mont'),
    # Tasks route
    webapp2.Route(r'/tasks/rates/update', handler=tasks.RatesUpdateTasks, handler_method='update', name='rates-update'),
    webapp2.Route(r'/tasks/rates/sync', handler=tasks.RatesUpdateTasks, handler_method='synchronize', name='rates-sync')
], debug=False)

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500
