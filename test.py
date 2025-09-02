import sys
import base64
from atlassian_api_py import controllerapi as conApi


USAGE = f"Usage: python {sys.argv[0]} [ --help | -key -rooturl -workspaceid ]"


# get system values
# tok = os.getenv('TOKEN')
# uname = os.getenv('ATLASSIAN_EMAIL')
# workspace_id = os.getenv('WORKSPACE_ID')
# key = base64.b64encode(f'{uname}:{tok}'.encode()).decode()

# Search using filter sql property
def _search_using_filter(controllerApi) -> list:
    getFilter = controllerApi.get_filter(10209)
    filterSql = getFilter['jql']
    isLast = False
    nextPageToken = ''
    keys = []
    while not isLast:
        search = controllerApi.search_jql(aJql=filterSql, nextPageToken=nextPageToken)
        if 'isLast' in search: isLast = search['isLast']
        if 'nextPageToken' in search: nextPageToken = search['nextPageToken']
        issues = search['issues']
        for item in issues:
            key = item['key']
            keys.append(key)
        print(len(keys))
        pass
    print()
    return keys


def _search_for_specific_issues(controllerApi, keys: list) -> None:
    for key in keys:
        getIssueDetails = controllerApi.get_issue(issueIdOrKey=key, fieldsByKeys=True)
        pass
        isLast = False
        startAt = 0
        changelogs = []
        while not isLast:
            getChangelog = controllerApi.get_changelogs(key)
            isLast = getChangelog['isLast']
            startAt = startAt + getChangelog['total']
            changelogs = changelogs + getChangelog['values']
            pass


def _create_workitem(controllerApi) -> str:
    fields = {
        "fields": {
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                    "type": "paragraph",
                    "content": [
                        {
                        "type": "text",
                        "text": "This was created using the atlassian-api-py library."
                        }
                    ]
                    }
                ]
            },
            "customfield_10010": "itdesk/aecdd25c-64df-4882-b24c-39d9c7c37bd9",
            "labels": [
                    "onsite"
            ],
            "priority": {
                "id": "3" # medium
            },

        }
    }
    issuetype = "Machine Activity"
    summary = "LT-D9FG6M3"
    newIssue = (controllerApi.create_single_workitem(issuetype, summary, fields)).json()
    print(f"New issue created with key: {newIssue['key']}")
    return newIssue['key']


def _search_projects(controllerApi):
    # look through results, will be paginated
    isLast = False
    startAt = 0
    total = 0
    print(f"{'Name':40}  {'Key':12}  {'Privacy':12}")
    while not isLast:
        projectsJson = controllerApi.get_project_search(startAt, typeKey = 'business,software')
        total = projectsJson['total']
        isLast = projectsJson['isLast']
        projectList = projectsJson['values']
        startAt = startAt + len(projectList)
        for project in projectList:
            projectId = project['id']
            projectKey = project['key']
            style = project['style']
            isPrivate = project['isPrivate']
            name = project['name']
            projectLeadId = ''
            projectLeadName = ''
            # get project details for private projects
            if not isPrivate:
                projectDetails = controllerApi.get_project_details(projectKey)
                pass
                # get project lead account Id
                projectLeadId = projectDetails['lead']['accountId']
                projectLeadName = projectDetails['lead']['displayName']
        
            print(f"{name:40}  {projectKey:12}  {isPrivate}  {projectLeadName:24}")


        pass


def main(args = None, opts = None) -> None:
    print("Welcome to `atlassian-api-py")

    print()

    if not args:
        raise SystemExit(USAGE)

    if args[0] == "--help":
        raise SystemExit(USAGE)
    
    if '-email' not in opts and \
        '-key' not in opts and \
        '-rooturl' not in opts:
        raise SystemExit(USAGE)
    
    email = args[opts.index('-email')]
    key = args[opts.index('-key')]
    rootUrl = args[opts.index('-rooturl')]
    workspaceId = ''

    print("==== CREDENTIALS ====")
    print(f"       email: {email}")
    print(f"         key: {key[0:5]}...")
    print(f"    root url: {rootUrl}")
    if '-workspaceid' in opts:
        workspaceId = args[opts.index('-workspaceid')]
        print(f"workspace ID: {workspaceId}")
    else:
        print(f"Workspace not provided, will be stored dynamically")
    print()

    token = base64.b64encode(f'{email}:{key}'.encode()).decode()
    print(f"generated token is: {token[0:5]}...")
    print()

    print(f"Testing credentials to {rootUrl}")
    print()

    print(f"Initialize API controller")
    controllerApi = conApi.ApiController(aToken=token, aRootUrl=rootUrl, aWorkspace=workspaceId)
    print()

    # print(f"Request all projects")
    # allProjectsRequest = controllerApi.get_all_projects()
    # print(f"Total projects found: {len(allProjectsRequest)}")
    # print()

    if False:
        print(f"Set a project")
        print(f"{controllerApi.set_project('ITDESK')}")

    if False: 
        print(f"Search using a filter")
        keys = _search_using_filter(controllerApi)

    if False:
        print("Seach for specific issues")
        _search_for_specific_issues(controllerApi, keys)

    if False:
        print("Create an issue")
        issueKey = _create_workitem(controllerApi)

    if True:
        print("Search projects")
        projectsJson = _search_projects(controllerApi=controllerApi)


if __name__ == "__main__":
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    main(args, opts)
