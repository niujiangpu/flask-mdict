#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import sys
import codecs
import logging
import argparse

import six

from stock.finance.stock import get_stock
from stock.finance.report import get_stock_values, \
    list_field, list_stock, list_market, list_plate

from rsttable import RstTable
import xlsxwriter


def list_main(args, parser):
    if args.field:
        all_field = list_field()
        for k, v in all_field.items():
            c = '%s [%s]' % (k, v['desc'])
            for field in v['fields']:
                print('%-20s' % c +
                    '%(name)s [%(desc)s (%(unit)s)]' % field)
    elif args.stock:
        data = list_stock()
        table = RstTable(data, header=False)
        print(table.table())
    elif args.market:
        data = list_market()
        table = RstTable(data, header=False)
        print(table.table())
    elif args.plate:
        data = list_plate()
        table = RstTable(data, header=False)
        print(table.table())
    else:
        parser.print_help()


def stock_main(args, parser):
    default_fields = [
        'mgjlr', 'yoy-mgjlr',
        'jlr', 'yoy-jlr',
        'yyzsr', 'yyzsrtbzzl',
        'jyxjllje', 'mom-jyxjllje', 'yoy-jyxjllje',
        'mgjzc', 'jzcsyl', 'zzcsyl', 'zcfzbl', 'xsmll',
        'chzzl', 'ch', 'mom-ch', 'yoy-ch',
        'tzsy_lrze', 'yywlr_lrze',
    ]

    if args.field:
        fields = args.field.split(',')
    else:
        fields = default_fields

    if not args.stock:
        parser.print_help()
        return

    book = None
    if args.output_xls:
        book = xlsxwriter.Workbook(args.output_xls)
        summary_sheet = book.add_worksheet('Summary')
        summary_row = 0

        num_format = book.add_format({
            'align': 'right',
            'num_format': '#,##0.00',
        })
        num_bold_format = book.add_format({
            'bold': True,
            'align': 'right',
            'num_format': '#,##0.00',
        })

        header_format = book.add_format({
            'bold': True,
            'align': 'left',
        })
        date_format = book.add_format({
            'align': 'left',
            'num_format': 'yyyy-mm-dd',
        })

    for mcode in args.stock:
        stock = get_stock(mcode)
        if not stock:
            print('Invalid MCODE: %s' % mcode)
            continue

        stock_info = []
        stock_info.append(stock.mcode)
        stock_info.append(stock.name)
        stock_info.append(stock.abbr)
        stock_info.append(stock.market.code)
        stock_info.append(stock.market.name)
        stock_info.append(stock.plate.code)
        stock_info.append(stock.plate.name)
        stock_info.append(u'%.2f 股' % stock.ltgb)
        stock_info.append(u'%.2f %%' % stock.ltgb_percent)

        data = get_stock_values(stock, fields)
        if book:
            summary_sheet.write_row(summary_row, 0, stock_info)
            summary_row += 1

            sheet = book.add_worksheet('%s %s' % (stock.mcode, stock.name))
            sheet.write_row(0, 0, data[0], date_format)
            for row in range(1, len(data)):
                sheet.write(row, 0, data[row][0], header_format)
                for column in range(1, len(data[0])):
                    fmt = num_format
                    if data[0][column].month == 12:
                        fmt = num_bold_format
                    sheet.write(row, column, data[row][column], fmt)
            sheet.set_column(0, 0, 20)
            sheet.set_column(1, len(data[0]), 12)
        else:
            title = ' '.join(stock_info)
            print(title)
            print('=' * (len(title) + RstTable.cjk_count(title)))
            table = RstTable(data)
            for row in range(table.row_count()):
                data_item = table.get_data(row, 0)
                if data_item.endswith('(%)') or data_item.endswith(u'元)'):
                    table.set_format('%0.2f', row, range(1, table.column_count()))
            print(table.table())
    if book:
        book.close()


def main(parser):
    args = parser.parse_args()

    if six.PY2:
        sys.stdout = codecs.getwriter(args.encoding)(sys.stdout)

    level = logging.WARNING - (args.verbose * 10)
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=level)

    if args.command == 'list':
        list_main(args, parser)
    elif args.command == 'stock':
        stock_main(args, parser)
    else:
        parser.print_help()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Inquire Finance Data')
    parser.add_argument('-v', '--verbose', help='verbose help',
                        action='count', default=1)
    parser.add_argument('--encoding', default='utf-8', help='Output terminal encoding. default: utf-8')

    subparsers = parser.add_subparsers(dest='command')

    list_parser = subparsers.add_parser('list')
    list_parser.add_argument('--field', action='store_true', help='list field name')
    list_parser.add_argument('--plate', action='store_true', help='list plate')
    list_parser.add_argument('--market', action='store_true', help='list market')
    list_parser.add_argument('--stock', action='store_true', help='list stock')

    stock_parser = subparsers.add_parser('stock')
    stock_parser.add_argument('--field', help='report field name')
    stock_parser.add_argument('--output-xls', help='output to xls')
    stock_parser.add_argument('stock',
                        nargs='+', help='stock code, "*" will match many characters')

    main(parser)
