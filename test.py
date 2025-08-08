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

    
def _create_issue(controllerApi) -> str:
    issue = {
        "fields": {
            "project": {
                "key": "TEST"
            },
            "summary": "Test issue created using atlassian-api-py",
            "description": "This is a test issue created using the atlassian-api-py library.",
            "issuetype": {
                "name": "Task"
            }
        }
    }
    newIssue = controllerApi.create_issue(issue)
    print(f"New issue created with key: {newIssue['key']}")
    return newIssue['key']


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

    print(f"Search using a filter")
    keys = _search_using_filter(controllerApi)

    print("Seach for specific issues")
    _search_for_specific_issues(controllerApi, keys)

    print("Create an issue")
    issueKey = _create_issue(controllerApi)


if __name__ == "__main__":
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    main(args, opts)
