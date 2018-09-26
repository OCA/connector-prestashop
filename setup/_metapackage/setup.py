import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-connector-prestashop",
    description="Meta package for oca-connector-prestashop Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-connector_prestashop',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
