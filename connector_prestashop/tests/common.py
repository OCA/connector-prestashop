# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import json
import logging

from contextlib import contextmanager

from os.path import dirname, exists, join

from vcr import VCR

import openerp.tests.common as common
from openerp.addons.connector.session import ConnectorSession


# secret.txt is a file which can be placed by the developer in the
# 'tests' directory. It contains the Prestashop URL on the first line
# and the API token on the second line.
# The secret.txt file must not be committed.
# The API token will be used to record the requests with vcr, but will not be
# stored in the fixtures files
prestashop_url = None
token = None
filename = join(dirname(__file__), 'secret.txt')
if exists(filename):
    with open(filename, 'r') as fp:
        assert len(fp.readlines()) == 2, "secret.txt must have 2 lines:" \
                "url, token"
        fp.seek(0)
        prestashop_url = next(fp).strip()
        token = next(fp).strip()


recorder = VCR(
    record_mode='once',
    cassette_library_dir=join(dirname(__file__), 'fixtures/cassettes'),
    path_transformer=VCR.ensure_suffix('.yaml'),
    match_on=['method', 'path', 'query'],
    filter_headers=['Authorization'],
)


@contextmanager
def quiet_logger(logger_path):
    logger = logging.getLogger(logger_path)
    level = logger.level
    logger.setLevel(logging.ERROR)
    yield
    logger.setLevel(level)


class PrestashopTransactionCase(common.TransactionCase):
    """ Base class for Tests with Prestashop """

    def setUp(self):
        super(PrestashopTransactionCase, self).setUp()
        self.conn_session = ConnectorSession.from_env(self.env)
        self.backend_record = self.env.ref(
            'connector_prestashop.prestashop_backend_demo'
        )
        self.backend_record.write({
            'location': prestashop_url,
            'webservice_key': token,
        })
        self.configure()
        recorder.register_matcher('json_body', self.check_json_body)

    def configure(self):
        # Default Prestashop currency is GBP
        self.env.ref('base.GBP').active = True

    def check_json_body(self, req1, req2):
        """ Check real request datas in addition to compare with cassette.

        By default, this matcher is only registered as 'json_body'.
        Need be added to recorder.match_on to be called.
        e.g:
            match_on = recorder.match_on + ('json_body',)
            with recorder.use_cassette(vcr_name, match_on=match_on):
               [....]
        """
        if req1.path != req2.path:
            return False

        return self._check_json_body(
            req1.path,
            json.loads(req1.body),
            json.loads(req2.body)
        )

    def _check_json_body(self, path, query_json, saved_json):
        """ Can be override.
        """
        return query_json == saved_json

    def assert_records(self, expected_records, records):
        """ Assert that a recordset matches with expected values.

        The expected records are a list of nametuple, the fields of the
        namedtuple must have the same name than the recordset's fields.

        The expected values are compared to the recordset and records that
        differ from the expected ones are show as ``-`` (missing) or ``+``
        (extra) lines.

        Example::

            ExpectedShop = namedtuple('ExpectedShop',
                                      'name company_id')
            expected = [
                ExpectedShop(
                    name='Shop1',
                    company_id=self.company_ch
                ),
                ExpectedShop(
                    name='Shop2',
                    company_id=self.company_ch
                ),
            ]
            self.assert_records(expected, shops)

        Possible output:

         - prestashop.shop(name: Shop1, company_id: res.company(2,))
         - prestashop.shop(name: Shop2, company_id: res.company(2,))
         + prestashop.shop(name: Shop3, company_id: res.company(1,))

        :param expected_records: list of namedtuple with matching values
                                 for the records
        :param records: the recordset to check
        :raises: AssertionError if the values do not match
        """
        model_name = records._model._name
        records = list(records)
        assert len(expected_records) > 0, "must have > 0 expected record"
        fields = expected_records[0]._fields
        not_found = []
        equals = []
        for expected in expected_records:
            for record in records:
                for field, value in expected._asdict().iteritems():
                    if not getattr(record, field) == value:
                        break
                else:
                    records.remove(record)
                    equals.append(record)
                    break
            else:
                not_found.append(expected)
        message = []
        for record in equals:
            # same records
            message.append(
                u' ✓ {}({})'.format(
                    model_name,
                    u', '.join(u'%s: %s' % (field, getattr(record, field)) for
                               field in fields)
                )
            )
        for expected in not_found:
            # missing records
            message.append(
                u' - {}({})'.format(
                    model_name,
                    u', '.join(u'%s: %s' % (k, v) for
                               k, v in expected._asdict().iteritems())
                )
            )
        for record in records:
            # extra records
            message.append(
                u' + {}({})'.format(
                    model_name,
                    u', '.join(u'%s: %s' % (field, getattr(record, field)) for
                               field in fields)
                )
            )
        if not_found or records:
            raise AssertionError(u'Records do not match:\n\n{}'.format(
                '\n'.join(message)
            ))

    def sync_metadata(self):
        with recorder.use_cassette('sync_metadata'):
            self.backend_record.synchronize_metadata()

    def sync_basedata(self):
        with recorder.use_cassette('sync_basedata'):
            self.backend_record.synchronize_basedata()

    def create_binding_no_export(self, model_name, openerp_id,
                                 prestashop_id=None, **cols):
        values = {
            'backend_id': self.backend_record.id,
            'openerp_id': openerp_id,
            'prestashop_id': prestashop_id,
        }
        if cols:
            values.update(cols)
        return self.env[model_name].with_context(
            connector_no_export=True
        ).create(values)

    def configure_taxes(self):
        company = self.env.ref('base.main_company')
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'general'})
        income_type = self.env.ref('account.data_account_type_revenue')
        expense_type = self.env.ref('account.data_account_type_expenses')
        receivable_type = self.env.ref('account.data_account_type_receivable')
        self.debit_account = self.env['account.account'].create({
            'company_id': company.id,
            'code': 'DB',
            'name': 'Debit Account',
            'user_type_id': income_type.id,
            'reconcile': False,
        })
        self.credit_account = self.env['account.account'].create({
            'company_id': company.id,
            'code': 'CR',
            'name': 'Credit Account',
            'user_type_id': expense_type.id,
            'reconcile': False,
        })
        self.receivable_account = self.env['account.account'].create({
            'company_id': company.id,
            'code': 'RA',
            'name': 'Receivable Account',
            'user_type_id': receivable_type.id,
            'reconcile': True,
        })
        self.env['ir.property'].search(
            [('name', '=', 'property_account_receivable_id'),
             ('res_id', '=', False)]
        ).value_reference = "account.account,%s" % self.receivable_account.id
        liabilities_account = self.env.ref(
            'account.data_account_type_current_liabilities'
        )
        self.tax_account = self.env['account.account'].create({
            'company_id': company.id,
            'code': 'tax',
            'name': 'Tax Account',
            'user_type_id': liabilities_account.id,
            'reconcile': False,
        })
        self.tax_20 = self.env['account.tax'].create({
            'name': '20.0%',
            'amount_type': 'percent',
            'amount': 20.0,
            'type_tax_use': 'sale',
            'company_id': company.id,
            'tax_group_id': self.env.ref('account.tax_group_taxes').id,
            'account_id': self.tax_account.id,
            'price_include': False,
        })
