import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-connector-prestashop",
    description="Meta package for oca-connector-prestashop Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-connector_prestashop',
        'odoo9-addon-connector_prestashop_catalog_manager',
        'odoo9-addon-connector_prestashop_manufacturer',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 9.0',
    ]
)
