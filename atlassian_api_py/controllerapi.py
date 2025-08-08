###############################################################################
# Wrap Atlassian API calls in Python classes.
###############################################################################
import requests
import json
from typing import Dict
from types import SimpleNamespace
from requests.auth import HTTPBasicAuth
import os


###############################################################################
# General API functions
###############################################################################
class ApiController():
    version = '2025Feb25a'
    __HEADERS: Dict[str, str]
    # ASSETS_URL = 'https://api.atlassian.com'


    # Initialize class
    def __init__(self, aToken, aRootUrl, aWorkspace = None, aProduction = None):
        self._TOKEN = aToken
        self._WORKSPACEID = aWorkspace
        self._PRODUCTION = aProduction
        self._ROOTURL = aRootUrl
        if self._WORKSPACEID == None or self._WORKSPACEID == '':
            self._WORKSPACEID = self.get_workspace_id()
            print(f"Workspace ID found: {self._WORKSPACEID}")
    

    def __callApi(self, mode, url, payload = None, query = None, headers = None):
        if headers == None:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Basic {self._TOKEN}'
            }

        attempts = 0
        while attempts < 3:
            attempts += 1
            response = requests.request(
                mode,
                url,
                data=payload,
                headers=headers,
                params=query
            )
            status = response.status_code
            if status // 100 == 2:
                break
            print(f"Api call attempt {attempts} failed, error {response.status_code}. {response.text}.\nTrying again.")
        
        return response
    

    ###########################################################################
    #
    # SYSTEM
    #
    ###########################################################################
    def get_workspace_id(self):
        w_url = f'{self._ROOTURL}/rest/servicedeskapi/assets/workspace'
        response = self.__callApi('GET', w_url)
        return response.json()['values'][0]['workspaceId']
    
        w_id_json = requests.get(
            w_url, 
            headers={'Accept':'application/json','Content-Type':'application/json','Authorization':f'Basic {self._TOKEN}'}
        )
        return w_id_json.json()['values'][0]['workspaceId']


    # set the project for this instance of controllerapi and populate
    # - issue types
    # - request types
    def set_project(self, projectId = None, projectKey = None):
        if projectId is not None:
            self.PROJECT_ID = projectId
        if projectKey is not None:
            self.PROJECT_KEY = projectKey

    ###########################################################################
    #
    # ASSETS
    #
    ###########################################################################
    # def search_schema(self, searchUrl, searchParameter):
    #     startAt = 0
    #     while True:
    #         response = self.__callApi('GET', url=searchUrl)
    #         responseJson = json.loads(response.text)
    #         if 'values' in responseJson: responseJson = responseJson['values']
    #         for item in responseJson:
    #             if item['name'] == searchParameter:
    #                 return item['id']
    #         if response['isLast'] == True:
    #             break
    #         startAt += response['maxResults']
    #     raise Exception("No matching schema found")


    # def get_schema_id(self, schemaName):
    #     url = f'{self.ASSETS_URL}/jsm/assets/workspace/{self._WORKSPACEID}/v1/objectschema/list'
    #     return self.search_schema(searchUrl=url, searchParameter=schemaName)


    # def get_object_id(self, schemaId, objectName):
    #     url = f'{self.ASSETS_URL}/jsm/assets/workspace/{self._WORKSPACEID}/v1/objectschema/{schemaId}/objecttypes'
    #     return self.search_schema(searchUrl=url, searchParameter=objectName)
    

    # def get_name_map(self, schemaId):
    #     url = f'{self.ASSETS_URL}/jsm/assets/workspace/{self._WORKSPACEID}/v1/objecttype/{schemaId}/attributes'
    #     response = self.__callApi('GET', url=url)
    #     return json.loads(response.text)


    # def post_aql_crawl(self, startAt, payload, maxResults = 25, includeAttributes = True):
    #     url = f'{self.ASSETS_URL}/jsm/assets/workspace/{self._WORKSPACEID}/v1/object/aql'

    #     query = {
    #         'startAt': f'{startAt}',
    #         'maxResults': f'{maxResults}',
    #         'includeAttributes': f'{includeAttributes}'
    #     }

    #     payload = json.dumps( {
    #         'qlQuery': f'{payload}'
    #     } )

    #     response = self.__callApi('POST', url=url, payload=payload, query=query)

    #     return json.loads(response.text)


    ###########################################################################
    #
    # Jira/JSM
    #
    ###########################################################################
    def __search_existing_ticket(self, projectId, summary, requestType):
        url = f'{self._ROOTURL}/rest/api/3/search'
        query = {
            'jql': f'project = {projectId} and ' \
                f'"Status Category[Dropdown]" != "Done" and ' \
                f'"Request Type" = "{requestType}" and ' \
                f'summary ~ "{summary}"',
            'expand': 'false'
        }
        return self.__callApi(mode='GET', url=url, query=query)


    def __create_ticket(self, summary, description, computers, requestType):
        url = f'{self._ROOTURL}/rest/api/3/issue'
        payload = json.dumps( {
            "fields": {
                "summary": summary,
                "description": description,
                "issuetype": {
                    "id": self.configDict[ApiConfig.ISSUE_TYPE_ID]
                },
                "customfield_10010": requestType,
                "labels": [
                    "jsm-assets"
                ],
                "priority": {
                    "id": "3" # medium
                },
                "project": {
                    "id": self.configDict[ApiConfig.PROJECT_ID]
                },
                "customfield_10170": computers
            }
        } )
        # check for existing ticket before creating a new one
        existingResponse = self.__search_existing_ticket(summary=summary, requestType=requestType)
        if (json.loads(existingResponse.text))['total'] > 0:
            # ticket exists
            # TODO make this work so we only respond with these three keys
            existingResponseJson = (json.loads(existingResponse.text))['issues'][0]
            temp = {
                "status_code": 200,
                "text": '{"id": "%(id)s", "key": "%(key)s", "self": "%(self)s"}' % {'id': existingResponseJson['id'], 'key': existingResponseJson['key'], 'self': existingResponseJson['self']}
                }
            temp = SimpleNamespace(**temp)
            return temp
        else:
            # ticket does not exist, create new ticket
            return self.__callApi(mode='POST', url=url, payload=payload)


    # create a single ticket in the project already set
    def create_single_ticket(self, summary, description):
        return self.__create_ticket(summary, description, self.configDict[ApiConfig.REQUEST_TYPE_VETTING])


    # # jsonBlobs : dictionary with two entries, summary & description
    # def create_bulk_tickets(self, jsonBlobs):
    #     for blob in jsonBlobs:
    #         return self.__create_ticket(blob['summary'], blob['description'], self.configDict[ApiConfig.REQUEST_TYPE_VETTING])
    

    # def edit_ticket(self, keyId, fields):
    #     url = f"https://qs-cloud.atlassian.net/rest/api/3/issue/{keyId}"

    #     return self.__callApi(
    #         "PUT",
    #         url=url,
    #         payload=fields
    #     )

    ##
    ## Filters
    ##

    # Returns a filter.
    # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-filters/#api-rest-api-3-filter-id-get
    # return
    #   
    def get_filter(self, filterId):
        endpointUrl = f"{self._ROOTURL}//rest/api/3/filter/{filterId}"
        response = self.__callApi(
            mode='GET',
            url=endpointUrl
        )
        return json.loads(response.text)


    ##
    ## Issue search
    ##

    # Search for issues using JQL enhanced search (GET)
    # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-get
    # return
    #   key ID of returned issues
    def search_jql(self,
                   aJql : str,
                   nextPageToken = None,
                   maxResults = 50,
                   fields = 'id',
                   expand = 'names'
                   ):
        endpointUrl = f"{self._ROOTURL}/rest/api/3/search/jql"
        query = {
            'jql': aJql,
            'nextPageToken': nextPageToken,
            'maxResults': f'{maxResults}',
            'fields': f'{fields}',
            'expand': f'{expand}'
            # 'reconcileIssues': '{reconcileIssues}'
        }
        response = self.__callApi(
            mode='GET',
            url=endpointUrl,
            query=query
        )
        return json.loads(response.text)
    

    # Get list of projects the current user has access to.
    # endpoint
    #   rest/api/3/project
    def get_all_projects(self):
        endpointUrl = f"{self._ROOTURL}/rest/api/3/project"
        response = self.__callApi(
            mode='GET',
            url=endpointUrl
        )
        # just return the response, API data is not needed
        return json.loads(response.text)
    

    ##
    ## Issues
    ##

    # Returns the details for an issue.
    # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get
    # endpoint
    #   rest/api/3/issue/{issueIdOrKey}
    def get_issue(self, issueIdOrKey, fieldsByKeys = False, expand = 'names'):
        endpointUrl = f"{self._ROOTURL}/rest/api/3/issue/{issueIdOrKey}"
        response = self.__callApi(
            mode='GET',
            url=endpointUrl,
            query={
                'fieldsByKeys' : fieldsByKeys,
                'expand' : expand
            }
        )
        return json.loads(response.text)
    
    # Returns a paginated list of all changelogs for an issue sorted by date, starting from the oldest.
    # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get
    # endpoint
    #   rest/api/3/issue/{issueIdOrKey}/changelog
    def get_changelogs(self, issueIdOrKey, startAt = 0, maxResults = 100):
        endpointUrl = f"{self._ROOTURL}/rest/api/3/issue/{issueIdOrKey}/changelog"
        response = self.__callApi(
            mode='GET',
            url=endpointUrl,
            query={
                'startAt' : startAt,
                'maxResults' : maxResults
            }
        )
        return json.loads(response.text)


if __name__ == "__main__":
    print("Unexpected call, expect calls directly through package imports.")
    