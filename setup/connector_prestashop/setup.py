import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                'vcr': 'vcrpy==1.10.5',
            },
        },
    },
)
