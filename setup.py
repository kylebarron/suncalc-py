#!/usr/bin/env python
"""The setup script."""

from setuptools import find_packages, setup

with open('README.md') as f:
    readme = f.read()

with open('CHANGELOG.md') as history_file:
    history = history_file.read()

requirements = ['numpy']
test_requirements = ['pytest', 'pandas']
setup_requirements = ['setuptools >= 38.6.0']

extra_reqs = {'pandas': ['pandas'], 'tests': test_requirements}

# yapf: disable
setup(
    author="Kyle Barron",
    author_email='kylebarron2@gmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="A fast, vectorized Python port of suncalc.js",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    keywords=['suncalc', 'sun'],
    name='suncalc',
    packages=find_packages(include=['suncalc', 'suncalc.*']),
    setup_requires=setup_requirements,
    extras_require=extra_reqs,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/kylebarron/suncalc-py',
    version='0.1.0',
    zip_safe=False,
)
