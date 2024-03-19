import re
import os
import sys
import time
import json
from getpass import getpass
import requests
from pathlib import Path
import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
nonce_pattern = re.compile("[a-f0-9]{64}")

def login(session, base_url, username, password):
    failed = re.compile("Your username or password is incorrect")
    r = req(session, "post", "/login", d={'name': username,
                                          'password': password,
                                          'nonce': csrf_token(session, base_url)})
    if (len(failed.findall(r.text)) > 0):
        print("Wrong username or password")
        sys.exit()


def grab_challenges(path, session):
    print("Grabbing challenges...")
    challenges = req(session, "get", "/api/v1/challenges").json()["data"]

    print("Found %s challenges" % len(challenges))
    for i, v in enumerate(challenges):
        chall_g = req(session, "get", "/api/v1/challenges/" + str(v["id"]))
        create_challenge(path, session, chall_g.json()["data"])
    print("Done!")
    session.close()


def setup(path):
    create_dir(path)
    print("CTF Folder created!")
    if (not os.path.exists(path / "readme.md")):
        open(path / "readme.md", 'a').close()
    os.system('git init ' + str(path))


def create_challenge(path, session, challenge):
    category = challenge["category"].lower()
    category_path = path / rep(category)
    create_dir(category_path)

    name = challenge["name"]
    points = challenge["value"]
    connect = challenge["connection_info"] if challenge["connection_info"] != None else ""
    challenge_name = (str(points) + "_" + rep(name)).lower()
    challenge_path = category_path / challenge_name
    create_dir(challenge_path)

    description = str(
        challenge["description"].strip().encode("utf-8"), 'utf-8')
    if (not os.path.exists(challenge_path / "readme.md")):
        with open(challenge_path / "readme.md", "w") as f:
            f.write('Name: %s \n' % name)
            f.write('Points: %s \n\n' % points)
            f.write('Description:\n%s \n\n' % description)
            f.write("Connection:\n%s  \n\n" % connect)
            f.write('Solution:\n')

    if (not os.path.exists(challenge_path / "flag")):
        open(challenge_path / "flag", 'a').close()

    files = challenge["files"]
    if (len(files) > 0):
        for i in files:
            fname = i.split("/")[3].split("?")[0]
            if (not os.path.exists(challenge_path / rep(fname))):
                d = req(session, "get", i)
                with open(challenge_path / rep(fname), 'wb') as f:
                    f.write(d.content)

def create_dir(path):
    try:
        if (not os.path.exists(path)):
            os.mkdir(path)
            print("%s created" % path)
    except OSError:
        print("Error creating %s" % path)


def req(session, method, url, d=None, j=None):

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
    headers = {'User-Agent': user_agent}

    if method == 'get':
        return session.get(base_url + url, allow_redirects=True, verify=False, headers=headers)
    if method == 'post':
        return session.post(base_url + url, data=d, json=j, verify=False, headers=headers)
    if method == 'jpost':
        headers = {'User-Agent': user_agent, 'CSRF-Token': csrf_token(session, base_url),
                   'Content-Type': 'application/json', 'Accept': 'application/json'}
        return session.post(base_url + url, data=d, json=j, verify=False, headers=headers)


def rep(string):
    badchars = [' ', '<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for i in badchars:
        string = string.replace(i, "_")
    return string

def csrf_token(session, base_url):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
    headers = {'User-Agent': user_agent}
    return nonce_pattern.findall(session.get(base_url, verify=False, headers=headers).text)[0]


if (len(sys.argv) != 4):
    print("usage: python3 autoctfd.py https://ctf_url username base_ctfs_dir")
    sys.exit()

base_url = sys.argv[1]
username = sys.argv[2]
based_ctf = sys.argv[3]

ctf_name = base_url.replace("https://", "").replace(".", "_")
ctf_path = Path(based_ctf + "/" + ctf_name + "_" + str(datetime.date.today().year))

setup(ctf_path)

password = getpass()
s = requests.Session()
login(s, base_url, username, password)

grab_challenges(ctf_path, s)
