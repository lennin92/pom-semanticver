import xml.etree.ElementTree as ET
import re


SEMANTIC_VERSION_PATTERN = r'(?P<major>[0-9]+).(?P<minor>[0-9]+).(?P<patch>[0-9]+)(\+(?P<build>[0-9]+))?'
SEMVER_PATTERN_STRING_VER = 'major.minor.patch+build'
REGEX_SEMANTIC_VERSION_PATTERN = re.compile(SEMANTIC_VERSION_PATTERN)
DIGIT_GROUPS = ['major', 'minor', 'patch', 'build']


def get_namespace(element):
  m = re.match('\{.*\}', element.tag)
  return m.group(0) if m else ''


def find_with_namespace(root, element):
    namespace = get_namespace(root)
    element = element.replace('/', '/{0}')
    if element.endswith('{0}'):
        element = element[:-3]
    return root.find(element.format(namespace))


def get_pom_current_version(root):
    ver = find_with_namespace(root, './version')
    if ver is None:
        return None
    return ver.text


def get_digit_version(current, update_digit):
    r = REGEX_SEMANTIC_VERSION_PATTERN.match(current)
    if r:
        dv = r.group(update_digit)
        return 0 if dv is None else dv
    else:
        return '0'


def get_next_digit(current):
    return 1 if current is None else int(current) + 1


def get_next_version(current_version, digit_to_update):
    version_final = SEMVER_PATTERN_STRING_VER
    if digit_to_update != 'build':
        version_final = version_final.replace('+build', '')
    for dg in DIGIT_GROUPS:
        current = get_digit_version(current_version, dg)
        # print(current_version, version_final, dg, current, digit_to_update,get_next_digit(current))
        if dg in version_final:
            version_final = version_final.replace(dg, str(current if dg!=digit_to_update else get_next_digit(current) ))
    return version_final


if __name__ == '__main__':
    import argparse
    from git import Repo
    import os

    parser = argparse.ArgumentParser(description='Updates pom to next version using semantic versioning and commits')
    parser.add_argument('--digit', help='Sets the digit to update valid values are [major, minor, patch, build]')
    parser.add_argument('--repo-url', help='Repository to clone and push after changing number')
    parser.add_argument('--repo-user', help='Repository user')
    parser.add_argument('--repo-pass', help='Repository password')
    parser.add_argument('--repo-branch', help='Repository branch')
    parser.add_argument('--prepend-commit-message', help='String to prepend to commit message ex(<prepend msg> updating version to {new version number})')
    parser.add_argument('--append-commit-message', help='String to append to commit message ex(updating version to {new version number} <append msg> )')

    args = parser.parse_args()
    print(args)

    project_dir = os.getcwd()
    repodir = os.path.join(project_dir, 'repo')
    if not os.path.exists(repodir) :
        os.mkdir(repodir)
    os.environ['GIT_ASKPASS'] = os.path.join(project_dir, 'askpass.py')
    os.environ['GIT_USERNAME'] = args.repo_user
    os.environ['GIT_PASSWORD'] = args.repo_pass
    url = args.repo_url
    repo = Repo.clone_from(url, repodir, branch= args.repo_branch)

    POM_DIR = os.path.join(repodir, 'pom.xml')
    tree = ET.parse(POM_DIR)
    root = tree.getroot()
    cur_ver = get_pom_current_version(root)
    # print(cur_ver)
    groups = ['major', 'minor', 'patch', 'build']
    for update in DIGIT_GROUPS:
        current = get_digit_version(cur_ver, update)
        next_digit = get_next_digit(current)
        # print('{0} = {1} -> {2}'.format(update, current, next_digit))

    digit = args.digit
    if digit not in groups:
        print("ERROR! Argument digit must be in ['major', 'minor', 'patch', 'build']")
        exit(0)

    next_version = get_next_version(cur_ver, digit)
    print('Actualizando {0} -> {1}'.format(cur_ver, next_version))
    ver = find_with_namespace(root, './version').text = next_version
    namespace = get_namespace(root)
    ET.register_namespace("", namespace.replace("{","").replace("}",""))
    tree.write("pom.xml")

    repo.git.add(update=True)
    COMMIT_MESSAGE = "[skip ci] {0} updating version to {1} {2} ".format(
        '' if args.prepend_commit_message is None else args.prepend_commit_message,
        next_version,
        '' if args.append_commit_message is None else args.append_commit_message,
    )
    repo.index.commit(COMMIT_MESSAGE)
    origin = repo.remote(name='origin')
    #origin.push()



