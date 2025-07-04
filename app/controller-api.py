###############################################################################
# Wrap Atlassian API calls in Python classes.
###############################################################################
import requests
import json
from typing import Dict
from types import SimpleNamespace
from requests.auth import HTTPBasicAuth


###############################################################################
# General API functions
###############################################################################
class ApiController():
    version = '2025Feb25a'
    __HEADERS: Dict[str, str]
    ASSETS_URL = 'https://api.atlassian.com'
    ROOT_URL = 'https://qs-cloud.atlassian.net'
    ROOT_SANDBOX_URL = 'https://qs-cloud-sandbox-525.atlassian.net'


    # Initialize class
    def __init__(self, aKey, aWorkspace = None, aProduction = None):
        self.key = aKey
        self.workspaceId = aWorkspace
        self.production = aProduction
        self.configDict = ApiConfig.getConfig(self.production)
        if self.workspaceId == None:
            self.workspaceId = self.get_workspace_id()
    

    def __callApi(self, mode, url, payload = None, query = None, headers = None):
        if headers == None:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Basic {self.key}'
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
        w_url = f'{self.ROOT_URL}/rest/servicedeskapi/assets/workspace'
        response = self.__callApi('GET', w_url)
        return response.json()['values'][0]['workspaceId']
    
        w_id_json = requests.get(
            w_url, 
            headers={'Accept':'application/json','Content-Type':'application/json','Authorization':f'Basic {self.key}'}
        )
        return w_id_json.json()['values'][0]['workspaceId']


    ###########################################################################
    #
    # ASSETS
    #
    ###########################################################################
    def search_schema(self, searchUrl, searchParameter):
        startAt = 0
        while True:
            response = self.__callApi('GET', url=searchUrl)
            responseJson = json.loads(response.text)
            if 'values' in responseJson: responseJson = responseJson['values']
            for item in responseJson:
                if item['name'] == searchParameter:
                    return item['id']
            if response['isLast'] == True:
                break
            startAt += response['maxResults']
        raise Exception("No matching schema found")


    def get_schema_id(self, schemaName):
        url = f'{self.ASSETS_URL}/jsm/assets/workspace/{self.workspaceId}/v1/objectschema/list'
        return self.search_schema(searchUrl=url, searchParameter=schemaName)


    def get_object_id(self, schemaId, objectName):
        url = f'{self.ASSETS_URL}/jsm/assets/workspace/{self.workspaceId}/v1/objectschema/{schemaId}/objecttypes'
        return self.search_schema(searchUrl=url, searchParameter=objectName)
    

    def get_name_map(self, schemaId):
        url = f'{self.ASSETS_URL}/jsm/assets/workspace/{self.workspaceId}/v1/objecttype/{schemaId}/attributes'
        response = self.__callApi('GET', url=url)
        return json.loads(response.text)


    def post_aql_crawl(self, startAt, payload, maxResults = 25, includeAttributes = True):
        url = f'{self.ASSETS_URL}/jsm/assets/workspace/{self.workspaceId}/v1/object/aql'

        query = {
            'startAt': f'{startAt}',
            'maxResults': f'{maxResults}',
            'includeAttributes': f'{includeAttributes}'
        }

        payload = json.dumps( {
            'qlQuery': f'{payload}'
        } )

        response = self.__callApi('POST', url=url, payload=payload, query=query)

        return json.loads(response.text)


    ###########################################################################
    #
    # Jira/JSM
    #
    ###########################################################################
    def __search_existing_ticket(self, summary, requestType):
        url = f'{self.configDict[ApiConfig.BASE]}/rest/api/3/search'
        query = {
            'jql': f'project = {self.configDict[ApiConfig.PROJECT_ID]} and ' \
                f'"Status Category[Dropdown]" != "Done" and ' \
                f'"Request Type" = "{requestType}" and ' \
                f'summary ~ "{summary}"',
            'expand': 'false'
        }
        return self.__callApi(mode='GET', url=url, query=query)


    def __create_ticket(self, summary, description, computers, requestType):
        url = f'{self.configDict[ApiConfig.BASE]}/rest/api/3/issue'
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


    def create_single_ticket(self, summary, description, computers):
        return self.__create_ticket(summary, description, computers, self.configDict[ApiConfig.REQUEST_TYPE_VETTING])


    # jsonBlobs : dictionary with two entries, summary & description
    def create_bulk_tickets(self, jsonBlobs):
        for blob in jsonBlobs:
            return self.__create_ticket(blob['summary'], blob['description'], self.configDict[ApiConfig.REQUEST_TYPE_VETTING])
    

    def edit_ticket(self, keyId, fields):
        url = f"https://qs-cloud.atlassian.net/rest/api/3/issue/{keyId}"

        return self.__callApi(
            "PUT",
            url=url,
            payload=fields
        )


if __name__ == "__main__":
    print("Unexpected call, expect calls directly through package imports.")
    