from distutils.core import setup

setup(
    name='python-wekan',
    version='0.1.1',
    packages=['tests', 'wekan'],
    url='https://github.com/bastianwenske/python-wekan',
    download_url='https://github.com/sarumont/py-trello',
    license='Apache License 2.0',
    author='Bastian Wenske',
    author_email='',
    description='This is a python client for interacting with the WeKan® REST-API',
    keywords='python',
    install_requires=["requests", "python-dateutil"],
    long_description_content_type="text/x-rst",
    long_description="""This is a python client for interacting with the WeKan® REST-API.
                        Each WeKan object is represented by a corresponding python object.
                     """
)
