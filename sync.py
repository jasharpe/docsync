import gdata.docs.data
import gdata.docs.client
import gdata.client
import gdata.gauth
import sys
import getpass
import os
import getopt
from BeautifulSoup import BeautifulSoup
from ftplib import FTP
import zipfile
import shutil

def usage():
  print '''-u for user name (i.e. email associated with Google account)
-t for title of page to download
-h is for host to upload results to
-f is to specify the ftp user name for the host
-d is for the destination folder on the host'''

def main(argv):
  user = None
  title = None
  domain = None
  ftp_user = None
  destination = None
  try:
    opts, args = getopt.getopt(argv[1:], "u:t:h:f:d:", ["user=", "title=", "host=", "ftpuser=", "destination="])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  for opt, arg in opts:
    if opt in ("-u", "--user"):
      user = arg
    elif opt in ("-t", "--title"):
      title = arg
    elif opt in ("-h", "--host"):
      domain = arg
    elif opt in ("-f", "--ftpuser"):
      ftp_user = arg
    elif opt in ("-d", "--destination"):
      if not arg[-1] == '/':
        destination = arg + '/'
      else:
        destination = arg
  if user is None:
    print "Must specify Google user."
    usage()
    sys.exit(2)
  if title is None:
    print "Must specify title."
    usage()
    sys.exit(2)
  if domain is None:
    print "Must specify host."
    usage()
    sys.exit(2)
  if ftp_user is None:
    print "Must specify ftp user."
    usage()
    sys.exit(2)
  if destination is None:
    print "Must specify destination."
    usage()
    sys.exit(2)

  client = getAuthenticatedClient(user)

  documents = client.GetEverything()
  success = False
  file_name = "".join((title + ".html").split(" "))
  for document_entry in documents:
    if document_entry.title.text == title:
      client.Export(document_entry, "tmp.zip")
      shutil.rmtree("tmp")
      unzip_file_into_dir("tmp.zip", "tmp")
      success = True
  if not success:
    print "Failed to find " + title + " on Google docs"
    sys.exit(2)

  # upload
  ftp = FTP(domain, ftp_user, getpass.getpass("ftp password for %s: " % domain))
  try:
    ftp.mkd(destination)
  except:
    pass
  ftp.storlines("STOR " + destination + file_name, open(os.path.join('tmp', file_name), "r"))
  try:
    ftp.mkd(destination + "images")
  except:
    pass
  for image in os.listdir(os.path.join('tmp', 'images')):
    ftp.storbinary("STOR " + destination + "images/" + image, open(os.path.join('tmp', 'images', image), "rb"))
  try:
    ftp.quit()
  except EOFError:
    ftp.close()

def unzip_file_into_dir(file, dir):
  os.mkdir(dir, 0777)
  z = zipfile.ZipFile(file)
  for name in z.namelist():
    this_dir = os.path.dirname(name)
    try:
      os.makedirs(os.path.join(dir, this_dir))
    except:
      pass
    if name.endswith('/'):
      os.mkdir(os.path.join(dir, name))
    else:
      outfile = open(os.path.join(dir, name), 'wb')
      outfile.write(z.read(name))
      outfile.close()

def getAuthenticatedClient(user):
  try:
    with open("token", "r") as f:
      auth_token = f.readline().strip()
      try:
        client = gdata.docs.client.DocsClient(auth_token=gdata.gauth.ClientLoginToken(auth_token), source='jasharpe-docssync-v1')
        client.ssl = True
        client.http_client.debug = False
        # check that we're authorized
        client.GetDocList(limit=0)
      except gdata.client.Unauthorized as e:
        print "Bad authentication information from saved token."
        raise e
  except (IOError, gdata.client.Unauthorized):
    client = gdata.docs.client.DocsClient(source='jsharpe-docssync-v1')
    client.ssl = True
    client.http_client.debug = False
    while 1:
      # get password
      password = getpass.getpass("password for %s: " % user)

      try:
        client.ClientLogin(user, password, client.source)
        break
      except gdata.client.BadAuthentication as e:
        print "Bad authentication information."

    f = open("token", "w")
    f.write(client.auth_token.token_string)
    f.close()
  return client


if __name__ == "__main__":
  main(sys.argv)
