import os, json
import onedrivesdk
from onedrivesdk.helpers import GetAuthCodeServer

file = open("./config.json").read()
file_json = json.loads(file)['env']

redirect_uri = file_json['redirect_uri']
client_secret = file_json['client_secret']

client = onedrivesdk.get_default_client(client_id=file_json['client_id'],
                                        scopes=['wl.signin',
                                                'wl.offline_access',
                                                'onedrive.readwrite'])

auth_url = client.auth_provider.get_auth_url(redirect_uri)

#this will block until we have the code
code = GetAuthCodeServer.get_auth_code(auth_url, redirect_uri)

client.auth_provider.authenticate(code, redirect_uri, client_secret)

# Get Brent Mac Doc Backup folder
startDir = client.item(drive="me", id="BCCC11629C5F7E3D!257166")


def createNewFolder(folderName, parent):
    f = onedrivesdk.Folder()
    i = onedrivesdk.Item()
    i.name = folderName
    i.folder = f
    # print("\n\n" + folderName)
    returned_item = parent.children.add(i)
    return client.item(drive="me", id=returned_item.id)


def getFolder(path, parent, cache={}):
    if path == ".":
        return parent

    if path.startswith("./"):
        # Remove ./
        path = path[2:]
    print path
    dirs = path.split("/", 1)
    topFolder = dirs[0]

    # Possible cache
    # if topFolder in cache:
    #     return getFolder()
    nextDir = None

    if parent.children:
        for child in parent.children.get():
            if child.name == topFolder:
                nextDir = client.item(drive="me", id=child.id)
                break
    if nextDir is None:
        nextDir = createNewFolder(topFolder, parent)
    # If we have reached the bottom folder
    if len(dirs) == 1:
        return nextDir
    else:
        return getFolder(dirs[1], nextDir)

# Iterate through Documents subfolder
os.chdir("/Users/shulmanbrent/Documents")
for root, dirs, files in os.walk("."):
    print "Uploading files from: ", root
    # Removes hidden directories and files
    files = [f for f in files if not f[0] == '.']
    dirs[:] = [d for d in dirs if not d[0] == '.']

    for f in files:
        if not f[0] == '.':
            folder = getFolder(root, startDir)
            if f not in [c.name for c in folder.children.get()]:
                folder.children[f].upload(os.path.join(root, f))
