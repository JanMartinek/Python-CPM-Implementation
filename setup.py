from setuptools import setup, find_packages


def _parse_requirements(file_path):
    requirements = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            requirement = line.split('#', 1)[0].strip()
            if requirement:
                requirements.append(requirement)
    return requirements

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

requirements = _parse_requirements('requirements.txt')

setup(
    name='cpm-python',
    version='1.0.0',
    author='CPM Implementation Team',
    author_email='',
    description='Common Provenance Model (CPM) - Python implementation based on W3C PROV-DM',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/JanMartinek/Python-CPM-Implementation',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'pytest-cov>=4.0.0',
            'jsonschema>=4.0.0',
            'lxml>=4.6.0',
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
    keywords='provenance cpm prov-dm w3c common-provenance-model',
    project_urls={
        'Documentation': 'https://github.com/JanMartinek/Python-CPM-Implementation/tree/main/docs',
        'Source': 'https://github.com/JanMartinek/Python-CPM-Implementation',
        'Bug Reports': 'https://github.com/JanMartinek/Python-CPM-Implementation/issues',
    },
)
