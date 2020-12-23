# © 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import functools
import logging
import os
from contextlib import contextmanager
from os.path import dirname, exists, join
from urllib import parse

from vcr import VCR

from odoo.addons.component.tests.common import SavepointComponentCase

_logger = logging.getLogger(__name__)
try:
    from prestapyt.xml2dict import xml2dict
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")

# secret.txt is a file which can be placed by the developer in the
# 'tests' directory. It contains the Prestashop URL on the first line
# and the API token on the second line.
# The secret.txt file must not be committed.
# The API token will be used to record the requests with vcr, but will not be
# stored in the fixtures files
prestashop_url = "http://localhost:8080"
token = "xxx"
filename = join(dirname(__file__), "secret.txt")
if not exists(filename):
    filename = os.environ.get("PS_TEST_WS_CREDENTIALS", "")
if exists(filename):
    _logger.debug("Using credentials file %s", filename)
    with open(filename, "r") as fp:
        assert len(fp.readlines()) == 2, "secret.txt must have 2 lines: url, token"
        fp.seek(0)
        prestashop_url = next(fp).strip()
        token = next(fp).strip()


def get_recorder(**kw):
    defaults = dict(
        record_mode="once",
        cassette_library_dir=join(dirname(__file__), "fixtures/cassettes"),
        path_transformer=VCR.ensure_suffix(".yaml"),
        match_on=["method", "path", "query"],
        filter_headers=["Authorization"],
        decode_compressed_response=True,
    )
    defaults.update(kw)
    return VCR(**defaults)


recorder = get_recorder()


@contextmanager
def quiet_logger(logger_path):
    logger = logging.getLogger(logger_path)
    level = logger.level
    logger.setLevel(logging.ERROR)
    yield
    logger.setLevel(level)


def assert_no_job_delayed(func):
    def _decorated(self, *args, **kwargs):
        job_count = self.env["queue.job"].search_count([])
        result = func(self, *args, **kwargs)
        self.assertEqual(
            job_count,
            self.env["queue.job"].search_count([]),
            "New jobs have been delayed during the test, this " "is unexpected.",
        )
        return result

    return functools.wraps(func)(_decorated)


class PrestashopTransactionCase(SavepointComponentCase):
    """ Base class for Tests with Prestashop """

    def setUp(self):
        super(PrestashopTransactionCase, self).setUp()
        self.backend_record = self.env.ref(
            "connector_prestashop.prestashop_backend_demo"
        )
        self.backend_record.write(
            {
                "location": prestashop_url,
                "webservice_key": token,
            }
        )
        self.configure()

    def configure(self):
        # Default Prestashop currency is GBP
        self.env.ref("base.GBP").active = True

    def base_mapping(self):
        self.create_binding_no_export("prestashop.res.lang", 1, 1, active=True)
        countries = [
            (self.env.ref("base.fr"), 8),
            (self.env.ref("base.uk"), 17),
            (self.env.ref("base.ch"), 19),
            (self.env.ref("base.us"), 21),
        ]
        for odoo_country, ps_country_id in countries:
            self.create_binding_no_export(
                "prestashop.res.country", odoo_country.id, ps_country_id
            )

    def assert_records(self, expected_records, records):
        """Assert that a recordset matches with expected values.

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

         The expected fields can follow record relations with the dotted
         notation style, but using '__' instead of '.'. Example::

            ExpectedShop = namedtuple('ExpectedShop',
                                      'name company_id__name')
            expected = [
                ExpectedShop(
                    name='Shop1',
                    company__name='Swiss Company',
                ),
            ]
            self.assert_records(expected, shops)


        :param expected_records: list of namedtuple with matching values
                                 for the records
        :param records: the recordset to check
        :raises: AssertionError if the values do not match
        """

        def get_record_field(record, field):
            attrs = field.split("__")
            for attr in attrs:
                record = record[attr]
            return record

        model_name = records._name
        records = list(records)
        assert len(expected_records) > 0, "must have > 0 expected record"
        fields = expected_records[0]._fields
        not_found = []
        equals = []
        for expected in expected_records:
            for record in records:
                for field, expected_value in expected._asdict().items():
                    record_value = get_record_field(record, field)
                    if not record_value == expected_value:
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
                u" ✓ {}({})".format(
                    model_name,
                    u", ".join(
                        u"%s: %s"
                        % (field.replace("__", "."), get_record_field(record, field))
                        for field in fields
                    ),
                )
            )
        for expected in not_found:
            # missing records
            message.append(
                u" - {}({})".format(
                    model_name,
                    u", ".join(
                        u"{}: {}".format(field.replace("__", "."), v)
                        for field, v in expected._asdict().items()
                    ),
                )
            )
        for record in records:
            # extra records
            message.append(
                u" + {}({})".format(
                    model_name,
                    u", ".join(
                        u"%s: %s"
                        % (field.replace("__", "."), get_record_field(record, field))
                        for field in fields
                    ),
                )
            )
        if not_found or records:
            raise AssertionError(
                u"Records do not match:\n\n{}".format("\n".join(message))
            )

    def sync_metadata(self):
        with recorder.use_cassette("sync_metadata"):
            self.backend_record.synchronize_metadata()

    def sync_basedata(self):
        with recorder.use_cassette("sync_basedata"):
            self.backend_record.synchronize_basedata()

    def create_binding_no_export(self, model_name, odoo_id, prestashop_id=None, **cols):
        values = {
            "backend_id": self.backend_record.id,
            "odoo_id": odoo_id,
            "prestashop_id": prestashop_id,
        }
        if cols:
            values.update(cols)
        return (
            self.env[model_name].with_context(connector_no_export=True).create(values)
        )

    @staticmethod
    def parse_path(url):
        return parse.urlparse(url).path

    @staticmethod
    def parse_qs(url):
        return parse.parse_qs(parse.urlparse(url).query)

    def configure_taxes(self):
        company = self.env.ref("base.main_company")
        self.journal = self.env["account.journal"].create(
            {"name": "Test journal", "code": "TEST", "type": "general"}
        )
        income_type = self.env.ref("account.data_account_type_revenue")
        expense_type = self.env.ref("account.data_account_type_expenses")
        receivable_type = self.env.ref("account.data_account_type_receivable")
        self.debit_account = self.env["account.account"].create(
            {
                "company_id": company.id,
                "code": "DB",
                "name": "Debit Account",
                "user_type_id": income_type.id,
                "reconcile": False,
            }
        )
        self.credit_account = self.env["account.account"].create(
            {
                "company_id": company.id,
                "code": "CR",
                "name": "Credit Account",
                "user_type_id": expense_type.id,
                "reconcile": False,
            }
        )
        self.receivable_account = self.env["account.account"].create(
            {
                "company_id": company.id,
                "code": "RA",
                "name": "Receivable Account",
                "user_type_id": receivable_type.id,
                "reconcile": True,
            }
        )
        self.env["ir.property"].search(
            [("name", "=", "property_account_receivable_id"), ("res_id", "=", False)]
        ).value_reference = ("account.account,%s" % self.receivable_account.id)
        liabilities_account = self.env.ref(
            "account.data_account_type_current_liabilities"
        )
        self.tax_account = self.env["account.account"].create(
            {
                "company_id": company.id,
                "code": "tax",
                "name": "Tax Account",
                "user_type_id": liabilities_account.id,
                "reconcile": False,
            }
        )
        self.tax_20 = self.env["account.tax"].create(
            {
                "name": "20.0%",
                "amount_type": "percent",
                "amount": 20.0,
                "type_tax_use": "sale",
                "company_id": company.id,
                "tax_group_id": self.env.ref("account.tax_group_taxes").id,
                "account_id": self.tax_account.id,
                "price_include": False,
            }
        )

    def _create_product_binding(
        self, name=None, template_ps_id=None, variant_ps_id=None
    ):
        product = self.env["product.product"].create(
            {
                "name": name,
                "type": "product",
            }
        )
        template = product.product_tmpl_id
        template_binding = self.create_binding_no_export(
            "prestashop.product.template",
            template.id,
            prestashop_id=template_ps_id,
            default_shop_id=self.shop.id,
        )
        return self.create_binding_no_export(
            "prestashop.product.combination",
            product.id,
            prestashop_id=variant_ps_id,
            main_template_id=template_binding.id,
        )

    @staticmethod
    def xmltodict(xml):
        return xml2dict(xml)


class ExportStockQuantityCase(PrestashopTransactionCase):
    def setUp(self):
        super(ExportStockQuantityCase, self).setUp()
        self.sync_metadata()
        self.base_mapping()
        self.shop_group = self.env["prestashop.shop.group"].search([])
        self.shop = self.env["prestashop.shop"].search([])

    def _change_product_qty(self, product, qty):
        location = (
            self.backend_record.stock_location_id
            or self.backend_record.warehouse_id.lot_stock_id
        )
        vals = {
            "location_id": location.id,
            "product_id": product.id,
            "new_quantity": qty,
        }
        qty_change = self.env["stock.change.product.qty"].create(vals)
        qty_change.with_context(
            active_id=product.id,
            connector_no_export=True,
        ).change_product_qty()
