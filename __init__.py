# This file is part stock_lot_last_expiration_date module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool

def register():
    Pool.register(
        module='stock_lot_last_expiration_date', type_='model')
    Pool.register(
        module='stock_lot_last_expiration_date', type_='wizard')
    Pool.register(
        module='stock_lot_last_expiration_date', type_='report')
