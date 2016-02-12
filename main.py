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

app = webapp2.WSGIApplication([
    webapp2.Route(r'/currencies', handler=handlers.Currencies, name='currency'),
    webapp2.Route(r'/currencies/<code:[a-z]{3}>', handler=handlers.Currencies, name='currencies-list'),
    webapp2.Route(r'/currencies/<currency:[a-z]{3}>/rates/today', handler=handlers.Rates, name='currency-rates-list'),
], debug=True)
