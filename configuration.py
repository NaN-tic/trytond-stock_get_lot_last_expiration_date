# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields


class StockConfiguration(metaclass=PoolMeta):
    __name__ = 'stock.configuration'
    shelf_life_delay_shipment_in = fields.TimeDelta(
        "Shelf Life Delay Shipment In")
    shelf_life_delay_shipment_in_return = fields.TimeDelta(
        "Shelf Life Delay Shipment In Return")
