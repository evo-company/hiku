import re
import os.path

from setuptools import setup, find_packages


with open(
    os.path.join(os.path.dirname(__file__), 'hiku', '__init__.py')
) as f:
    VERSION = re.match(r".*__version__ = '(.*?)'", f.read(), re.S).group(1)

with open(
    os.path.join(os.path.dirname(__file__), 'README.rst')
) as f:
    DESCRIPTION = f.read()

setup(
    name='hiku',
    version=VERSION,
    description='Library to implement Graph APIs',
    long_description=DESCRIPTION,
    long_description_content_type='text/x-rst',
    author='Vladimir Magamedov',
    author_email='vladimir@magamedov.com',
    url='https://github.com/vmagamedov/hiku',
    packages=find_packages(exclude=['test*']),
    include_package_data=True,
    license='BSD-3-Clause',
    python_requires='>=3.5',
    install_requires=[],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
