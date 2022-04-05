import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='tastypiex',
    version='0.2',
    packages=find_packages(),
    include_package_data=True,
    license='MIT',  # example license
    description='tastypie extensions',
    long_description=README,
    url='http://www.shrebo.com/',
    author='Patrick Senti',
    author_email='patrick.senti@shrebo.ch',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: Commercial',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # replace these appropriately if you are using Python 3
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'Django<3',
        'django-tastypie>=0.14.3',
        'docutils==0.15',
    ],
    extras_require={
      'swagger': [
          'django-tastypie-swagger@git+https://github.com/miraculixx/django-tastypie-swagger.git',
      ]
    },
    dependency_links=[
    ]
)
