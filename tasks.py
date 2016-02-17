# -*- coding: utf-8 -*-
from webapp2 import RequestHandler
from models import Config, Rate, Currency

MONTHS = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12}


class RatesUpdateTask(RequestHandler):
    def get(self):
        import json
        import xlrd
        from urllib2 import urlopen
        from datetime import date

        source = Config.get_by_id('source').value or None
        sheet_name = Config.get_by_id('sheet_name').value or None
        columns = json.loads(Config.get_by_id('columns').value or '{}')
        last_row = Config.get_by_id('last_row')

        initial_row = int(last_row.value) or 3
        last_processed = initial_row

        threashold = 100

        if source:
            source_file = urlopen(source)
            with xlrd.open_workbook(file_contents=source_file.read()) as book:
                # Getting the sheet to work with
                sheet = book.sheet_by_name(sheet_name=sheet_name)
                total_records = sheet.nrows
                last_processed = initial_row

                if initial_row < total_records:
                    for rowIndex in range(initial_row, ((initial_row + threashold) if (initial_row + threashold) < total_records else total_records)):
                        for currency, colIndex in columns.items():
                            # if currency not in results:
                            #     results[currency] = []

                            col_value = sheet.cell_value(rowx=rowIndex, colx=colIndex)

                            if col_value is not '':
                                year = int(sheet.cell_value(rowx=rowIndex, colx=0))
                                month = MONTHS.get((sheet.cell_value(rowx=rowIndex, colx=1) or '').lower(), None)
                                day = int(sheet.cell_value(rowx=rowIndex, colx=2))

                                if year and month and day:
                                    try:
                                        rate_date = date(year, month, day)
                                    except ValueError:
                                        continue

                                    cur = Currency.get_by_id(currency)

                                    # results[currency].append({'date': record_date.toordinal(), 'value': col_value})
                                    rate = Rate(currency=cur.key, date=rate_date, value=col_value)
                                    rate.put()

                        last_processed = rowIndex

                    # Updating the "last_row" processed
                    last_row.value = str(last_processed + 1)
                    last_row.put()

        return self.response.write(u'Total processed: ' + str((last_processed + 1) - initial_row))
