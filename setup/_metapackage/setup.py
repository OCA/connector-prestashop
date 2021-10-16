import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-connector-prestashop",
    description="Meta package for oca-connector-prestashop Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-connector_prestashop',
        'odoo8-addon-connector_prestashop_catalog_manager',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 8.0',
    ]
)
