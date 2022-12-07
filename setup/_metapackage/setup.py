import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-connector-prestashop",
    description="Meta package for oca-connector-prestashop Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-connector_prestashop',
        'odoo14-addon-connector_prestashop_environment',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
