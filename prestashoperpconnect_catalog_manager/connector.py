

from openerp.osv import orm


class prestashoperpconnect_catalog_manager_installed(orm.AbstractModel):
    """Empty model used to know if the module is installed on the
    database.

    If the model is in the registry, the module is installed.
    """
    _name = 'prestashoperpconnect_catalog_manager.installed'
