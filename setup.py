"""
Integration testing for ChatOps via Slack
"""
from setuptools import find_packages, setup

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError, OSError):
    long_description = open('README.md').read()

dependencies = ['click', 'pyyaml', 'requests', 'websocket-client', 'slackclient']

setup(
    name='periskop',
    version='1.0.0',
    url='https://github.com/unic/periskop',
    license='Apache License 2.0',
    author='Unic AG - Robert Erdin, Mathias Petermann, Nicolas Baer',
    author_email='cloud@unic.com',
    description='Integration testing for ChatOps via Slack',
    long_description=long_description,
    packages=["periskop"],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'periskop = periskop.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
