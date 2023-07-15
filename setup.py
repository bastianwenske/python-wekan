from distutils.core import setup

setup(
    name='python-wekan',
    version='0.1.8',
    packages=['tests', 'wekan'],
    url='https://github.com/bastianwenske/python-wekan',
    download_url='https://github.com/bastianwenske/python-wekan',
    license='BSD 3-Clause License',
    author='Bastian Wenske',
    author_email='',
    description='This is a python client for interacting with the WeKan® REST-API',
    keywords='python',
    install_requires=["requests", "python-dateutil"],
    long_description_content_type="text/markdown",
    long_description=open('README.md').read()
)
