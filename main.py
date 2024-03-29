import sys
import requests
import datetime
import json
from deep_translator import GoogleTranslator
import os

from src.BannerGenerator import BannerGenerator

VERSION = "1.0.1"

GITHUB_NAME = ""
OUTPUT_FILE = ""
TIMESTAMP_FILE = ""
LOG_FILE = ""
LOG_LENGTH = -1
QUIETLY = False
PROJECT_META_FILES = []
BANNER_PATH = ""
FORCE = False
DEV_MODE = False

projects = []
log_lines = []
timestamp = datetime.datetime.now()


def main():
    set_args()
    print_intro()
    read_log()
    log_props()

    repos = get_github_repos()
    log(f"Found {len(repos)} repos for user {GITHUB_NAME}")
    for repo in repos:
        meta_data = get_project_file(repo)
        if meta_data is None:
            continue

        create_project_dict(repo, meta_data)

    if not FORCE and not has_changes():
        log("No changes detected!")
        log("Exiting...")
        sys.exit(0)

    save_projects()
    generate_banner(projects)
    save_timestamp()
    save_log()
    if not DEV_MODE:
        push()
    log("", False)
    log("Finished!", False)
    log("Have a nice day :)", False)
    log("by Philipp B.", False)
    sys.exit(0)

def push():
    os.system("sh push.sh")

def log_props():
    log("---")
    log(f"Github name: {GITHUB_NAME}")
    log(f"Output file: {OUTPUT_FILE}")
    log(f"Looking for project files: {PROJECT_META_FILES}")
    if LOG_FILE != "":
        log(f"Log file: {LOG_FILE}")
        if LOG_LENGTH < 0:
            log("Log length: unlimited")
        else:
            log(f"Log length: {LOG_LENGTH}")
    else:
        log("No log file specified!")

    if TIMESTAMP_FILE != "":
        log(f"Timestamp file: {TIMESTAMP_FILE}")
    else:
        log("No timestamp file specified!")
    log()


def set_args():
    conf_file = ""
    for i in range(len(sys.argv)):
        arg = sys.argv[i].lower()
        if (arg == "-name" or arg == "-n") and i+1 < len(sys.argv):
            global GITHUB_NAME
            GITHUB_NAME = sys.argv[i+1]
        if (arg == "-banner") and i+1 < len(sys.argv):
            global BANNER_PATH
            BANNER_PATH = sys.argv[i+1]
        elif (arg == "-output" or arg == "-o") and i+1 < len(sys.argv):
            global OUTPUT_FILE
            OUTPUT_FILE = sys.argv[i+1]
        elif (arg == "-files" or arg == "-f") and i+1 < len(sys.argv):
            global PROJECT_META_FILES
            PROJECT_META_FILES = sys.argv[i+1].split(",")
        elif (arg == "-read" or arg == "-r") and i+1 < len(sys.argv):
            conf_file = sys.argv[i+1]
        elif (arg == "-logfile" or arg == "-lf") and i+1 < len(sys.argv):
            global LOG_FILE
            LOG_FILE = sys.argv[i+1]
        elif (arg == "-loglength" or arg == "-ll") and i+1 < len(sys.argv):
            global LOG_LENGTH
            try:
                LOG_LENGTH = int(sys.argv[i+1])
            except Exception:
                print("Error: Log length must be an integer!")
                sys.exit(1)
        elif (arg == "-quiet" or arg == "-q"):
            global QUIETLY
            QUIETLY = True
        elif (arg == "-dev" ):
            global DEV_MODE
            DEV_MODE = True
        elif (arg == "-force" ):
            global FORCE
            FORCE = True
        elif (arg == "-timestamp" or arg == "-ts") and i+1 < len(sys.argv):
            global TIMESTAMP_FILE
            TIMESTAMP_FILE = sys.argv[i+1]
        elif (arg == "-help" or arg == "-h"):
            print_intro(False)
            print_help()
            sys.exit(0)
        elif (arg == "-version" or arg == "-v"):
            print_intro(False)
            print(f"Version: {VERSION}")
            sys.exit(0)

    # read config file
    if conf_file != "":
        if not os.path.isfile(conf_file):
            print("Error: Config file does not exist!")
            sys.exit(1)
        try:
            txt = open(conf_file, "r").read()
        except Exception:
            print("Error: Could not read config file!")
            sys.exit(1)

        # convert config file to dict
        data = convert_conf_file(txt)
        if data.get("name"):
            GITHUB_NAME = data["name"]
        if data.get("output"):
            OUTPUT_FILE = data["output"]
        if data.get("project_files"):
            PROJECT_META_FILES = data["project_files"].split(",")
        if data.get("timestamp"):
            TIMESTAMP_FILE = data["timestamp"]
        if data.get("banner"):
            BANNER_PATH = data["banner"]
        if data.get("log_file"):
            LOG_FILE = data["log_file"]
        if data.get("log_length"):
            try:
                LOG_LENGTH = int(data["log_length"])
            except Exception:
                print("Error: Log length must be an integer!")
                sys.exit(1)

    # check if all required arguments are set
    if GITHUB_NAME == "":
        print("Error: No github name specified!")
        sys.exit(1)
    if OUTPUT_FILE == "":
        print("Error: No output file specified!")
        sys.exit(1)
    if len(PROJECT_META_FILES) == 0:
        print("Error: No project meta files specified!")
        sys.exit(1)

    if DEV_MODE:
        # join paths
        if BANNER_PATH != "":
            BANNER_PATH = os.path.join("dev", BANNER_PATH)
        OUTPUT_FILE = os.path.join("dev", OUTPUT_FILE)
        LOG_FILE = os.path.join("dev", LOG_FILE)
        TIMESTAMP_FILE = os.path.join("dev", TIMESTAMP_FILE)
        


def create_project_dict(repo, meta_data):
    project = {}
    name = repo["name"]
    branch = repo["default_branch"]
    project["name"] = name
    project["branch"] = branch
    project["url"] = repo["html_url"]
    project["homepage"] = repo["homepage"]
    project["topics"] = repo["topics"]
    project["stars"] = repo["stargazers_count"]
    project["description"] = repo["description"]

    meta_data = convert_conf_file(meta_data)
    if len(meta_data.keys()) > 0:
        log(f"Project {name} has meta data: {meta_data}")
    else:
        log(f"Project {name} has no meta data")

    if meta_data.get("description_translate") and repo["description"] != "" and repo["description"] is not None:
        translate_list = meta_data.get("description_translate").split(",")
        for to in translate_list:
            try:
                project["description_" + to] = GoogleTranslator(
                    source='auto', target=to).translate(repo["description"])
            except Exception:
                log(f"Could not translate description to {to}")
                project["description_" + to] = ""
    elif meta_data.get("translate_description") and repo["description"] != "" and repo["description"] is not None:
        translate_list = meta_data.get("translate_description").split(",")
        for to in translate_list:
            try:
                project["description_" + to] = GoogleTranslator(
                    source='auto', target=to).translate(repo["description"])
            except Exception:
                log(f"Could not translate description to {to}")
                project["description_" + to] = ""

    if meta_data.get("logo"):
        project["logo_url"] = f"https://raw.githubusercontent.com/{GITHUB_NAME}/{name}/{branch}/" + meta_data["logo"]
    else:
        project["logo_url"] = ""

    if meta_data.get("logo_small"):
        project["logo_small_url"] = f"https://raw.githubusercontent.com/{GITHUB_NAME}/{name}/{branch}/" + \
            meta_data["logo_small"]
    else:
        project["logo_small_url"] = ""

    if meta_data.get("version"):
        project["version"] = meta_data["version"]
    else:
        project["version"] = ""
    if not meta_data.get("ignore"):
        if meta_data.get("priority") or meta_data.get("prio"):
            projects.insert(0, project)
        else:
            projects.append(project)
    else:
        log(f"Ignoring project {name}")
    log()

def has_changes():
    old_Projects = []
    if not os.path.isfile(OUTPUT_FILE):
        return True
    try:
        old_Projects = json.load(open(OUTPUT_FILE, "r"))
    except Exception:
        return True
    if len(old_Projects) != len(projects):
        return True
    for project in projects:
        if not project in old_Projects:
            return True
    return False
        

def convert_conf_file(txt):
    data = {}
    divider = ":"
    for line in txt.splitlines():
        if line.strip().startswith("#?"):
            divider = line.strip().replace("#?", "")
            continue
        if line == "" or line.startswith("#"):
            continue
        if not divider in line:
            data[line.strip().lower()] = line.strip()
            continue
        key, value = line.split(divider, 1)
        data[key.strip().lower()] = value.strip()
    return data


def get_project_file(repo):
    name = repo["name"]
    branch = repo["default_branch"]
    for file_name in PROJECT_META_FILES:
        url = f"https://raw.githubusercontent.com/{GITHUB_NAME}/{name}/{branch}/{file_name}"
        response = requests.get(url)
        if response.status_code == 200:
            log(f"Found project {name} ({file_name})...")
            return response.text
    return None


def get_github_repos():
    response = requests.get(
        f"https://api.github.com/users/{GITHUB_NAME}/repos")
    if response.status_code != 200:
        print("Error: Could not get repos from github!")
        sys.exit(1)
    repos = response.json()
    return repos


def save_projects():
    log(f"Saving {len(projects)} projects to {OUTPUT_FILE}...")
    if not os.path.isfile(OUTPUT_FILE):
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
    with open(OUTPUT_FILE, "w", encoding='utf8') as outfile:
        json.dump(projects, outfile, indent=4, ensure_ascii=False)
    log("Done!", False)


def save_timestamp():
    if not os.path.isfile(OUTPUT_FILE):
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(TIMESTAMP_FILE, "w") as outfile:
        # write timestamp to file
        outfile.write(f"{str(timestamp)}\n")
    log("Timestamp: " + str(timestamp))


def read_log():
    if LOG_FILE == "":
        return
    try:
        with open(LOG_FILE, "r") as infile:
            for line in infile.readlines():
                log_lines.append(line.strip())
    except Exception:
        log("Could not read log file!", False)


def save_log():
    if LOG_FILE == "":
        return
    try:
        with open(LOG_FILE, "w") as outfile:
            for line in log_lines:
                outfile.write(line + "\n")
    except Exception:
        log("Could not save log file!", False)


def log(txt="", to_file=True):
    if not QUIETLY:
        print(txt)
    if LOG_FILE != "" and to_file and txt != "":
        log_lines.append(f"[{str(timestamp)}] {txt}")
        if LOG_LENGTH > 0 and len(log_lines) > LOG_LENGTH:
            while len(log_lines) > LOG_LENGTH:
                log_lines.pop(0)

def generate_banner(projects):
    if BANNER_PATH == "":
        return
    log(f"Generating banner from {len(projects)} projects...")
    bg = BannerGenerator(BANNER_PATH, GITHUB_NAME)
    bg.generate_images(projects)
    bg.save()
    log("Banner saved to " + BANNER_PATH)

def print_help():
    print("Usage: python main.py [flags]")
    print("")
    print("Flags:")
    print("  -name, -n <github-name>        Github name of the user")
    print("  -output, -o <file>             Name of the output file")
    print("  -files, -f <file1,file2,...>   Name of the project meta files")
    print("  -read, -r <file>               Read config file")
    print("  -ts, -timestamp <file>         Name of the timestamp file")
    print("  -quiet, -q                     Do not print anything to the console")
    print("  -force                         Execute even if there are no changes")
    print("  -help, -h                      Print this help")
    print("  -version, -v                   Print the version number")
    print("  -banner <path-to-file>         Generate a banner from the projects in the file")
    print("  -dev                           Run in dev mode")


def print_intro(note_quietly=True):
    if note_quietly and QUIETLY:
        return
    print("""
          
          *************************
          *** .project-provider ***
          *************************
          
          """)


if __name__ == "__main__":
    main()
