# This file is part stock_lot_health_alert module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import stock

def register():
    Pool.register(
        configuration.StockConfiguration,
        stock.Location,
        stock.Lot,
        stock.Move,
        module='stock_lot_health_alert', type_='model')
    Pool.register(
        module='stock_lot_health_alert', type_='wizard')
    Pool.register(
        module='stock_lot_health_alert', type_='report')
