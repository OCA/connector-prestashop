# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import contextmanager

import psycopg2


from odoo import _, exceptions
from odoo.addons.component.core import AbstractComponent

from odoo.addons.queue_job.job import job
from odoo.addons.queue_job.job import related_action
from odoo.addons.connector.exception import RetryableJobError
from .mapper import TranslationPrestashopExportMapper


_logger = logging.getLogger(__name__)


# Exporters for PrestaShop.
# In addition to its export job, an exporter has to:
# * check in PrestaShop if the record has been updated more recently than the
#  last sync date and if yes, delay an import
# * call the ``bind`` method of the binder to update the last sync date


class PrestashopBaseExporter(AbstractComponent):
    """ Base exporter for PrestaShop """

    _name = 'prestashop.base.exporter'
    _inherit = ['base.exporter', 'base.prestashop.connector']
    _usage = 'record.exporter'

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(PrestashopBaseExporter, self).__init__(environment)
        self.prestashop_id = None
        self.binding_id = None

    def _get_binding(self):
        """ Return the raw Odoo data for ``self.binding_id`` """
        return self.model.browse(self.binding_id)

    def run(self, binding_id, *args, **kwargs):
        """ Run the synchronization

        :param binding_id: identifier of the binding record to export
        """
        self.binding_id = binding_id
        self.binding = self._get_binding()
        self.prestashop_id = self.binder.to_external(self.binding)
        result = self._run(*args, **kwargs)

        self.binder.bind(self.prestashop_id, self.binding)
        # commit so we keep the external ID if several cascading exports
        # are called and one of them fails
        self.session.commit()
        self._after_export()
        return result

    def _run(self, *args, **kwargs):
        """ Flow of the synchronization, implemented in inherited classes"""
        raise NotImplementedError

    def _after_export(self):
        """Create records of dependants prestashop objects"""
        return


class PrestashopExporter(AbstractComponent):
    """ A common flow for the exports to PrestaShop """

    _name = 'prestashop.exporter'
    _inherit = 'prestashop.base.exporter'

    _openerp_field = 'odoo_id'

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(PrestashopExporter, self).__init__(environment)
        self.binding = None

    def _has_to_skip(self):
        """ Return True if the export can be skipped """
        return False

    @contextmanager
    def _retry_unique_violation(self):
        """ Context manager: catch Unique constraint error and retry the
        job later.

        When we execute several jobs workers concurrently, it happens
        that 2 jobs are creating the same record at the same time (binding
        record created by :meth:`_export_dependency`), resulting in:

            IntegrityError: duplicate key value violates unique
            constraint "prestashop_product_template_openerp_uniq"
            DETAIL:  Key (backend_id, odoo_id)=(1, 4851) already exists.

        In that case, we'll retry the import just later.

        """
        try:
            yield
        except psycopg2.IntegrityError as err:
            if err.pgcode == psycopg2.errorcodes.UNIQUE_VIOLATION:
                raise RetryableJobError(
                    'A database error caused the failure of the job:\n'
                    '%s\n\n'
                    'Likely due to 2 concurrent jobs wanting to create '
                    'the same record. The job will be retried later.' % err)
            else:
                raise

    def _get_or_create_binding(
            self, relation, binding_model,
            binding_field_name='prestashop_bind_ids',
            bind_values=None):
        binding = None
        # wrap is typically True if the relation is a 'product.product'
        # record but the binding model is 'prestashop.product.product'
        wrap = relation._model._name != binding_model
        if wrap and hasattr(relation, binding_field_name):
            domain = [(self._openerp_field, '=', relation.id),
                      ('backend_id', '=', self.backend_record.id)]
            model = self.env[binding_model].with_context(active_test=False)
            binding = model.search(domain)
            if binding:
                binding.ensure_one()
            else:
                # we are working with a unwrapped record (e.g.
                # product.template) and the binding does not exist yet.
                # Example: I created a product.product and its binding
                # prestashop.product.product, it is exported, but we need to
                # create the binding for the template.

                _bind_values = {'backend_id': self.backend_record.id,
                                self._openerp_field: relation.id}
                _bind_values.update(bind_values or {})
                # If 2 jobs create it at the same time, retry
                # one later. A unique constraint (backend_id,
                # odoo_id) should exist on the binding model
                with self._retry_unique_violation():
                    model_c = self.env[binding_model].sudo().with_context(
                        connector_no_export=True
                    )
                    binding = model_c.create(_bind_values)
                    # Eager commit to avoid having 2 jobs
                    # exporting at the same time.
                    self.session.commit()
        else:
            # If prestashop_bind_ids does not exist we are typically in a
            # "direct" binding (the binding record is the same record).
            # If wrap is True, relation is already a binding record.
            binding = relation
        return binding

    def _export_dependency(self, relation, binding_model,
                           exporter_class=None,
                           component_usage='record.exporter',
                           binding_field_name='prestashop_bind_ids',
                           bind_values=None, force_sync=False):
        """
        Export a dependency. The exporter class is a subclass of
        ``PrestashopExporter``.  A more precise class can be defined.

        When a binding does not exist yet, it is automatically created.

        .. warning:: a commit is done at the end of the export of each
                     dependency. The reason for that is that we pushed a record
                     on the backend and we absolutely have to keep its ID.

                     So you *must* take care to not modify the Odoo database
                     except when writing back the external ID or eventual
                     external data to keep on this side.

                     You should call this method only in the beginning of the
                     exporter synchronization (in `~._export_dependencies`)
                     and do not write data which should be rollbacked in case
                     of error.

        :param relation: record to export if not already exported
        :type relation: :py:class:`openerp.models.BaseModel`
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param exporter_cls: :py:class:`openerp.addons.connector.\
                                        connector.ConnectorUnit`
                             class or parent class to use for the export.
                             By default: PrestashopExporter
        :type exporter_cls: :py:class:`openerp.addons.connector.\
                                       connector.MetaConnectorUnit`
        :param component_usage: 'usage' to look for to find the Component to
                                for the export, by default 'record.exporter'
        :param binding_field_name: name of the one2many towards the bindings
                                   default is 'prestashop_bind_ids'
        :type binding_field_name: str | unicode
        :param bind_values: override values used to create a new binding
        :type bind_values: dict
        :param force_sync: force update of already sync'ed item
        :type force_sync: bool
        """
        if not relation:
            return

        binding = self._get_or_create_binding(
            relation, binding_model,
            binding_field_name=binding_field_name,
            bind_values=bind_values)

        rel_binder = self.binder_for(binding_model)

        if not rel_binder.to_external(binding) or force_sync:
            exporter = self.component(usage=component_usage,
                                      model_name=binding_model)
            exporter.run(binding)
        return binding

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        return

    def _map_data(self):
        """ Convert the external record to Odoo """
        return self.mapper.map_record(self.binding)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``Model.create`` or
        ``Model.update`` if some fields are missing

        Raise `InvalidDataError`
        """
        return

    def _create(self, data):
        """ Create the PrestaShop record """
        return self.backend_adapter.create(data)

    def _update(self, data):
        """ Update an PrestaShop record """
        assert self.prestashop_id
        return self.backend_adapter.write(self.prestashop_id, data)

    def _lock(self):
        """ Lock the binding record.

        Lock the binding record so we are sure that only one export
        job is running for this record if concurrent jobs have to export the
        same record.

        When concurrent jobs try to export the same record, the first one
        will lock and proceed, the others will fail to lock and will be
        retried later.

        This behavior works also when the export becomes multilevel
        with :meth:`_export_dependencies`. Each level will set its own lock
        on the binding record it has to export.

        Uses ``NO KEY UPDATE``, to avoid FK accesses
        being blocked in PSQL > 9.3.
        """
        sql = ("SELECT id FROM %s WHERE ID = %%s FOR NO KEY UPDATE NOWAIT" %
               self.model._table)
        try:
            self.env.cr.execute(sql, (self.binding_id,),
                                log_exceptions=False)
        except psycopg2.OperationalError:
            _logger.info('A concurrent job is already exporting the same '
                         'record (%s with id %s). Job delayed later.',
                         self.model._name, self.binding_id)
            raise RetryableJobError(
                'A concurrent job is already exporting the same record '
                '(%s with id %s). The job will be retried later.' %
                (self.model._name, self.binding_id))

    def _run(self, fields=None, **kwargs):
        """ Flow of the synchronization, implemented in inherited classes"""
        assert self.binding_id
        assert self.binding

        if not self.binding.exists():
            return _('Record to export does no longer exist.')

        if self._has_to_skip():
            return

        # export the missing linked resources
        self._export_dependencies()

        # prevent other jobs to export the same record
        # will be released on commit (or rollback)
        self._lock()

        map_record = self._map_data()

        if self.prestashop_id:
            record = map_record.values()
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self._update(record)
        else:
            record = map_record.values(for_create=True)
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self.prestashop_id = self._create(record)
            if self.prestashop_id == 0:
                raise exceptions.Warning(
                    _("Record on PrestaShop have not been created"))

        message = _('Record exported with ID %s on PrestaShop.')
        return message % self.prestashop_id


class TranslationPrestashopExporter(AbstractComponent):

    _name = 'translation.prestashop.exporter'
    _inherit = 'prestashop.exporter'

    @property
    def mapper(self):
        if self._mapper is None:
            self._mapper = self.connector_env.get_connector_unit(
                TranslationPrestashopExportMapper)
        return self._mapper


def related_action_record(session, job):
    binding_model = job.args[0]
    binding_id = job.args[1]
    record = session.env[binding_model].browse(binding_id)
    odoo_name = record.odoo_id._name

    action = {
        'name': _(odoo_name),
        'type': 'ir.actions.act_window',
        'res_model': odoo_name,
        'view_type': 'form',
        'view_mode': 'form',
        'res_id': record.odoo_id.id,
    }
    return action


@job(default_channel='root.prestashop')
@related_action(action=related_action_record)
def export_record(session, model_name, binding_id, fields=None, **kwargs):
    """ Export a record on PrestaShop """
    # TODO: FIX PRESTASHOP do not support partial edit
    fields = None
    record = session.env[model_name].browse(binding_id)
    env = record.backend_id.get_environment(model_name, session=session)
    exporter = env.get_connector_unit(PrestashopExporter)
    return exporter.run(binding_id, fields=fields, **kwargs)
