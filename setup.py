from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='cpm-python',
    version='1.0.0',
    author='CPM Implementation Team',
    author_email='',
    description='Chain Provenance Model (CPM) - Python Implementation based on W3C PROV-DM',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/your-repo/python-implementation-of-the-cpm',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'pytest-cov>=4.0.0',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    keywords='provenance cpm prov-dm w3c chain-provenance-model',
    project_urls={
        'Documentation': 'https://github.com/your-repo/python-implementation-of-the-cpm',
        'Source': 'https://github.com/your-repo/python-implementation-of-the-cpm',
        'Bug Reports': 'https://github.com/your-repo/python-implementation-of-the-cpm/issues',
    },
)
