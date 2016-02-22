# -*- coding: utf-8 -*-
import json
from urllib2 import urlopen
from datetime import date
from google.appengine.ext import ndb

from google.appengine.runtime.apiproxy_errors import OverQuotaError
import webapp2
import xlrd

from models import Config, Rate, Currency

MONTHS = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12}


class RatesUpdateTasks(webapp2.RequestHandler):
    def update(self):
        source = Config.get_by_id('rates_source').value or None
        sheet_name = Config.get_by_id('rates_sheet_name').value or None
        columns = json.loads(Config.get_by_id('rates_columns').value or '{}')
        last_row = Config.get_by_id('rates_last_row')

        initial_row = int(last_row.value) or 3
        last_processed = initial_row

        threshold = 100

        if source:
            source_file = urlopen(source)
            with xlrd.open_workbook(file_contents=source_file.read()) as book:
                # Getting the sheet to work with
                sheet = book.sheet_by_name(sheet_name=sheet_name)
                total_records = sheet.nrows
                last_processed = initial_row

                if initial_row < total_records:
                    rate_list = []
                    processed = False
                    for rowIndex in range(initial_row, ((initial_row + threshold) if (initial_row + threshold) < total_records else total_records)):
                        year = int(sheet.cell_value(rowx=rowIndex, colx=0))
                        month = int(MONTHS.get((sheet.cell_value(rowx=rowIndex, colx=1) or '').lower(), None))
                        day = int(sheet.cell_value(rowx=rowIndex, colx=2))

                        rate_date = date(year, month, day) if year and month and day else None

                        if rate_date:
                            for currency, colIndex in columns.items():
                                col_value = sheet.cell_value(rowx=rowIndex, colx=colIndex)

                                if col_value is not '':
                                    # Verify if already exists a rate in the db
                                    if not Rate.query(Rate.currency == ndb.Key('Currency', currency), Rate.date == rate_date).count():
                                        rate_list.append(Rate(currency=ndb.Key('Currency', currency), date=rate_date, value=col_value))
                                        processed = True

                        last_processed = rowIndex
                        if processed:
                            if (last_processed - initial_row) >= threshold:
                                break

                    if len(rate_list) > 0:
                        ndb.put_multi(rate_list)

                    # Updating the "last_row" processed
                    last_row.value = str(last_processed + 1)
                    last_row.put()

        return self.response.write(u'Total processed: ' + str((last_processed + 1) - initial_row))

    def synchronize(self):
        source = Config.get_by_id('rates_source').value or None
        sheet_name = Config.get_by_id('rates_sheet_name').value or None
        columns = json.loads(Config.get_by_id('rates_columns').value or '{}')
        last_row = Config.get_by_id('rates_last_sync_row')

        initial_row = int(last_row.value) or 3
        last_processed = initial_row

        threshold = 20

        if source:
            source_file = urlopen(source)
            with xlrd.open_workbook(file_contents=source_file.read()) as book:
                # Getting the sheet to work with
                sheet = book.sheet_by_name(sheet_name=sheet_name)
                total_records = sheet.nrows
                last_processed = initial_row

                if initial_row < total_records:
                    rate_list = []
                    for rowIndex in range(initial_row, total_records):
                        processed = False
                        year = int(sheet.cell_value(rowx=rowIndex, colx=0))
                        month = int(MONTHS.get((sheet.cell_value(rowx=rowIndex, colx=1) or '').lower(), None))
                        day = int(sheet.cell_value(rowx=rowIndex, colx=2))

                        rate_date = date(year, month, day) if year and month and day else None

                        if rate_date:
                            for currency, colIndex in columns.items():
                                col_value = sheet.cell_value(rowx=rowIndex, colx=colIndex)

                                if col_value is not '':
                                    # Verify if already exists a rate in the db
                                    if not Rate.query(Rate.currency == ndb.Key('Currency', currency), Rate.date == rate_date).count():
                                        rate_list.append(Rate(currency=ndb.Key('Currency', currency), date=rate_date, value=col_value))
                                        processed = True

                        last_processed = rowIndex
                        if processed:
                            threshold -= 1
                            if threshold == 0:
                                break

                    if len(rate_list) > 0:
                        ndb.put_multi(rate_list)

                    # Updating the "last_row" processed
                    last_row.value = str(last_processed + 1)
                    last_row.put()

        return self.response.write(u'Last processed line: ' + str(last_processed + 1))
