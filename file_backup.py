import os, json, time
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
checkTime = False

def createNewFolder(folderName, parent):
    f = onedrivesdk.Folder()
    i = onedrivesdk.Item()
    i.name = folderName
    i.folder = f
    returned_item = parent.children.add(i)
    return client.item(drive="me", id=returned_item.id)


def getFolder(path, parent, root="", cache={}):
    if path == ".":
        return parent

    if path.startswith("./"):
        # Remove ./
        path = path[2:]
    dirs = path.split("/", 1)
    topFolder = dirs[0]

    # Check cache
    #####################
    i = 1
    temp_path = path[:]
    pth_splt = temp_path.rsplit("/", i)
    while len(pth_splt) > 1:
        p = pth_splt[0]
        if p in cache:
            return getFolder("/".join(pth_splt[1:]), client.item(drive="me", id=cache[p]), root=p)
        i += 1
        pth_splt = temp_path.rsplit(",", i)
    #####################

    nextDir = None

    if parent.children:
        for child in parent.children.get():
            if child.name == topFolder:
                nextDir = client.item(drive="me", id=child.id)
                break

    if nextDir is None:
        nextDir = createNewFolder(topFolder, parent)

    # Add to cache
    new_root = os.path.join(root, nextDir.get().name)
    print "Root added to cache: ", new_root
    cache[new_root] = nextDir.get().id
    # If we have reached the bottom folder
    if len(dirs) == 1:
        return nextDir
    else:
        return getFolder(dirs[1], nextDir, root=new_root)


def getDateOneDrive(fileName, children):
    for child in children:
        if child.name == fileName:
            # child = client.item(drive="me", id=child.id)
            return child.created_date_time
    return None


# Iterate through Documents subfolder
os.chdir("/Users/shulmanbrent/Documents")
for root, dirs, files in os.walk("."):
    print "Uploading files from: ", root
    # Removes hidden directories and files
    # files = [f for f in files if not f[0] == '.']
    dirs[:] = [d for d in dirs if not d[0] == '.']
    
    try:    
        folder = getFolder(root, startDir)
    except Exception:
        continue
    for i, f in enumerate(files):
        if i < 25:
            continue
        if not f[0] == '.':
            children = None
            try:
                children = folder.children.get()
            except Exception:
                continue
            if all(c.name != f for c in children):
                try:
                    print "Uploading ", repr(f)
                    folder.children[f].upload(os.path.join(root, f))
                except Exception:
                    continue
            elif checkTime:
                # Check if the file has been edited
                try:
                    dateEditedOneDrive = getDateOneDrive(f, children)
                    dateEditedOneDrive = time.mktime(dateEditedOneDrive.timetuple())
                    dateEditedLocal = os.path.getmtime(os.path.join(root, f))
                    if int(dateEditedLocal) > int(dateEditedOneDrive):
                        print "Uploading ", f
                        folder.children[f].upload(os.path.join(root, f))
                    else:
                        print "Has not been edited: ", f
                except Exception:
                    continue
