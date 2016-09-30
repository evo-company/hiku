from setuptools import setup, find_packages

setup(
    name='Hiku',
    version='0.1.0',
    description='Declarative data presentation library',
    author='Vladimir Magamedov',
    author_email='vladimir@magamedov.com',
    url='https://github.com/vmagamedov/hiku',
    packages=find_packages(),
    include_package_data=True,
    license='BSD',
    install_requires=[],
    extras_require={
        'sqlalchemy': ['sqlalchemy'],
        'graphql': ['graphql-core'],
    }
)
