from setuptools import setup

setup(
   name='atlassian-api-py',
   version='0.1',
   description='Wrapper for Jira API',
   author='Kurt Anderson',
   author_email='akurt6805@protonmail.com',
   packages=['atlassian-api-py'],  #same as name
   install_requires=['certifi', 'charset-normalizer', 'idna', 'requests', 'urllib3'], #external packages as dependencies
)