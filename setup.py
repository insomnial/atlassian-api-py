from setuptools import setup

setup(
   name='atlassian_api_py',
   version='0.5',
   description='Wrapper for Jira API',
   author='Kurt Anderson',
   author_email='akurt6805@protonmail.com',
   packages=['atlassian_api_py'],  #same as name
   install_requires=['certifi', 'charset-normalizer', 'idna', 'requests', 'urllib3'], #external packages as dependencies
)
