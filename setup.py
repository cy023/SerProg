# -*- coding: utf-8 -*-

import serprog
import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

with open('requirements.txt','r') as f:
    install_requires = f.read().split('\n')
    install_requires.remove('')

setuptools.setup(
    name = 'serprog',
    version = serprog.__version__,
    description = 'A serial and secure programming tool for microcontroller.',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    author = 'cy023',
    author_email = 'cyyang023@gmail.com',
    url = 'https://github.com/cy023/SerProg',
    license = 'MIT',
    packages = ['serprog'],
    zip_safe = False,
    entry_points = {
        'console_scripts': [
            'serprog = serprog.__main__:run'
        ],
    },
    install_requires = install_requires
)
