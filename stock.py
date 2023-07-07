# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If, Bool
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserError

CHECK_HEALTH_ALERT_TRUE = ['group_stock_lot_td', 'group_stock_lot_qd']
MODIFY_HEALTH_ALERT_LOT = ['group_stock_lot_td']
MODIFY_LOT = MODIFY_HEALTH_ALERT_LOT + ['group_stock_lot_admin']


class HealthAlertGroupControl(object):
    __slots__ = ()

    @classmethod
    def in_group(cls, fs_ids):
        pool = Pool()
        Group = pool.get('res.group')
        User = pool.get('res.user')
        ModelData = pool.get('ir.model.data')

        groups = []
        for fs_id in fs_ids:
            try:
                module, model = fs_id.split('.', 1)
            except ValueError:
                module, model = ('stock_lot_health_alert', fs_id)
            groups.append(Group(ModelData.get_id(module, model)))
        transaction = Transaction()
        user_id = transaction.user
        if user_id == 0:
            user_id = transaction.context.get('user', user_id)
        if user_id == 0:
            return True
        user = User(user_id)
        return bool(set(groups) & set(user.groups))


class Location(metaclass=PoolMeta):
    __name__ = 'stock.location'
    allow_health_alert = fields.Boolean('Allow Health Alert',
        help='Check this option to allow lots with health alert to this '
             'location.')


class Lot(HealthAlertGroupControl, metaclass=PoolMeta):
    __name__ = 'stock.lot'
    health_alert = fields.Boolean('Health Alert',
        help='Check this option if the lot is in health alert')

    @classmethod
    def __setup__(cls):
        super(Lot, cls).__setup__()

    def get_rec_name(self, name):
        rec_name = super(Lot, self).get_rec_name(name)
        if self.health_alert:
            rec_name += ' (%s)' % gettext('stock_lot_health_alert.health_alert')
        return rec_name

    @classmethod
    def delete(cls, lots):
        if cls.in_group(MODIFY_LOT):
            for lot in lots:
                if lot.health_alert:
                    raise UserError(
                            gettext('stock_lot_health_alert.msg_remove_lot_health_alert',
                            lot=lot.number))
        else:
            raise UserError(
                gettext('stock_lot_health_alert.msg_remove_lot'))
        super(Lot, cls).delete(lots)

    @classmethod
    def write(cls, *args):
        actions = iter(args)
        for lots, values in zip(actions, actions):
            if ('health_alert' not in values and
               not cls.in_group(MODIFY_LOT)):
                raise UserError(
                    gettext('stock_lot_health_alert.msg_modify_lot'))

            if (values.get('health_alert', False)
                    and (not cls.in_group(CHECK_HEALTH_ALERT_TRUE)
                        or (len(values.keys()) > 1
                            and not cls.in_group(MODIFY_HEALTH_ALERT_LOT)))):
                    raise UserError(
                            gettext('stock_lot_health_alert.msg_edit_lot_health_alert_true',
                            lots=", ".join([l.number for l in lots])))
            elif (not values.get('health_alert', True) and
                    not cls.in_group(MODIFY_HEALTH_ALERT_LOT)):
                raise UserError(
                        gettext('stock_lot_health_alert.msg_edit_lot_health_alert',
                        lots=", ".join([l.number for l in lots])))
        super(Lot, cls).write(*args)

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            if (vals.get('health_alert', False) and
                    not cls.in_group(CHECK_HEALTH_ALERT_TRUE)):
                raise UserError(
                    gettext('stock_lot_health_alert.msg_create_lot_health_alert'))
        return super(Lot, cls).create(vlist)

    @classmethod
    def copy(cls, lots, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default.setdefault('health_alert', False)
        return super(Lot, cls).copy(lots, default=default)


class Move(HealthAlertGroupControl, metaclass=PoolMeta):
    __name__ = 'stock.move'
    lot_last_expiration_date = fields.Function(
        fields.Date("Lot Last Experiration Date"),
        'get_lot_last_expiration_date')

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        cls.lot.domain += [If(
                ((Eval('state') == 'draft') & Bool(Eval('lot_last_expiration_date'))),
                ('expiration_date', '>', Eval('lot_last_expiration_date')), ())]
        cls.lot.depends |= {'state', 'lot_last_expiration_date'}
        cls.lot.context['stock_date_date'] = If(
            Bool(Eval('effective_date', False)),
            Eval('effective_date'),
            Eval('planned_date'))
        cls.lot.context['locations'] = [Eval('from_location')]
        cls.lot.depends.add('from_location')

    @classmethod
    def validate(cls, moves):
        for move in moves:
            move.check_allow_lot_in_health_alert()
        super(Move, cls).validate(moves)

    def check_allow_lot_in_health_alert(self):
        if self.to_location.allow_health_alert or not self.lot:
            return

        if not self.to_location.allow_health_alert and self.lot.health_alert:
            raise UserError(
                    gettext('stock_lot_health_alert.msg_health_alert_lot_invalid_destination',
                    move=self.rec_name, lot=self.lot.rec_name,
                    to_location=self.to_location.rec_name))

    @classmethod
    def delete(cls, moves):
        for move in moves:
            if (move.lot and move.lot.health_alert and
                    not cls.in_group(MODIFY_HEALTH_ALERT_LOT)):
                raise UserError(
                    gettext('stock_lot_health_alert.msg_remove_move_health_alert',
                    name=move.product.name))
        super(Move, cls).delete(moves)

    @classmethod
    def write(cls, *args):
        pool = Pool()
        Lot = pool.get('stock.lot')
        actions = iter(args)
        for moves, values in zip(actions, actions):
            lot = values.get('lot', None)
            lot = Lot(lot) if lot else None
            if (lot and lot.health_alert and
                    not cls.in_group(MODIFY_HEALTH_ALERT_LOT)):
                raise UserError(
                    gettext('stock_lot_health_alert.msg_edit_move_health_alert',
                    names=", ".join([m.product.name for m in moves])))
        super(Move, cls).write(*args)

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Lot = pool.get('stock.lot')
        Product = pool.get('product.product')
        for vals in vlist:
            lot = vals.get('lot', None)
            lot = Lot(lot) if lot else None
            if (lot and lot.health_alert and
                    not cls.in_group(MODIFY_HEALTH_ALERT_LOT)):
                product = Product(vals['product'])
                raise UserError(
                        gettext('stock_lot_health_alert.msg_create_move_health_alert',
                        name=product.name))
        return super(Move, cls).create(vlist)

    @classmethod
    def get_lot_last_expiration_date(cls, moves, name):
        pool = Pool()
        Config = pool.get('stock.configuration')
        ShipmentIn = pool.get('stock.shipment.in')
        ShipmentInReturn = pool.get('stock.shipment.in.return')
        Date = pool.get('ir.date')

        config = Config(1)
        delay_shipment_in = config.shelf_life_delay_shipment_in
        delay_shipment_in_return = config.shelf_life_delay_shipment_in_return

        today = Date.today()

        res = dict((x.id, None) for x in moves)
        for move in moves:
            if not move.shipment or move.product.expiration_state == 'none':
                continue
            if delay_shipment_in and isinstance(move.shipment, ShipmentIn):
                res[move.id] = today - delay_shipment_in
            elif delay_shipment_in_return and isinstance(move.shipment, ShipmentInReturn):
                res[move.id] = today - delay_shipment_in_return
        return res
