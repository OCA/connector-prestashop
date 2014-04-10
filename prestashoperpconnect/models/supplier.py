from openerp.osv import fields, orm


class res_partner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'prestashop_supplier_bind_ids': fields.one2many(
            'prestashop.supplier',
            'openerp_id',
            string="Prestashop supplier bindings",
        ),
    }


class prestashop_supplier(orm.Model):
    _name = 'prestashop.supplier'
    _inherit = 'prestashop.binding'
    _inherits = {'res.partner': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'res.partner',
            string='Partner',
            required=True,
            ondelete='cascade'
        ),
    }
