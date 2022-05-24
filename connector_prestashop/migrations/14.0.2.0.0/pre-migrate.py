# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute(
        """
            SELECT rel.relname, con.conname
            FROM pg_catalog.pg_constraint con
            INNER JOIN pg_catalog.pg_class rel
                ON rel.oid = con.conrelid
            INNER JOIN pg_catalog.pg_namespace nsp
                ON nsp.oid = connamespace
            WHERE con.conname ilike '%prestashop_erp_uniq%';
        """
    )
    for constraint in cr.fetchall():
        cr.execute(f"ALTER TABLE {constraint[0]} DROP CONSTRAINT {constraint[1]}")
