from builtins import open
from os import path
from setuptools import setup, find_packages


BASE_DIR = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(BASE_DIR, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='pyjexl',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.3.0',

    description='A JEXL parser and evaluator.',
    long_description=long_description,

    # So it formats the README markdown on pypi.org
    long_description_content_type='text/markdown',

    # The project's main homepage.
    url='https://github.com/mozilla/pyjexl',

    # Author details
    author='Mythmon',
    author_email='mcooper@mozilla.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],

    # What does your project relate to?
    keywords='jexl parser',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['parsimonious', 'future'],

    # So that you can run `python setup.py test`.
    tests_require=['pytest'],
    setup_requires=['pytest-runner'],
)
