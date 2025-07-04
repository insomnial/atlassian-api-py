import sys
import base64
from app import controllerapi as conApi


USAGE = f"Usage: python {sys.argv[0]} [ --help | -key -rooturl -workspaceid ]"


# get system values
# tok = os.getenv('TOKEN')
# uname = os.getenv('ATLASSIAN_EMAIL')
# workspace_id = os.getenv('WORKSPACE_ID')
# key = base64.b64encode(f'{uname}:{tok}'.encode()).decode()


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

    print(f"Request all projects")
    allProjectsRequest = controllerApi.get_all_projects()
    print(f"Total projects found: {len(allProjectsRequest)}")

    print()


if __name__ == "__main__":
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    main(args, opts)
