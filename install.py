#!/usr/bin/env python

import requests
from subprocess import *
from bs4 import BeautifulSoup
import time
import json


def exit_install(msg, rc, se, so):
    print(msg)
    print(se)
    print(so)
    exit(rc)


def run_cmd(cmd, **kwargs):
    decode = kwargs.get('decode', True)
    verbose = kwargs.get('verbose', False)
    env = kwargs.get('env', None)
    timeout = kwargs.get('timeout', None)

    res = Popen(cmd,
                stdout=PIPE,
                stderr=STDOUT,
                env=env)
    so, se = res.communicate(timeout=timeout)

    if decode:
        if so:
            so = so.decode('utf-8')
        else:
            so = []
        if se:
            se = se.decode('utf-8')
        else:
            se = []

    rc = res.returncode

    if verbose:
        print("CMD", cmd)
        print("rc:", rc)
        print("se:", se)
        print("so:", so)
    return rc, se, so


def check_file(fname):
    """
    returns: True if fname is found
    """
    rc, se, so = run_cmd(['ls', "-l", fname])
    return not rc


def file_content(fname):
    rc, se, so = run_cmd(["cat", fname])
    if not rc:
        return so
    else:
        return ''


def get_env_vars():
    res = dict()
    for line in file_content(".env").splitlines():
        if "=" in line:
            k, v = line.split("=")
            res[k] = v
    return res


def check_dot_env_config():
    print("Checking .env variables...", end='')
    if not check_file(".env"):
        print("Missing .env, please refer to documentation")
        exit(1)
    env_var_list = set([
        "SUPERPASS",
        "PG_DB",
        "SECRET_KEY",
        "WEB_PORT"
    ])
    defined_vars = set([k for k, v in get_env_vars().items() if v])
    missing_vars = env_var_list.difference(defined_vars)
    if missing_vars:
        print(f".env is missing variables: {missing_vars}")
        exit(2)

    print("ok")
    extra_defined_vars = defined_vars - env_var_list
    if extra_defined_vars:
        print(f"WARNING: These variables are not used {extra_defined_vars}")


def check_docker():
    print("Checking docker...", end="")
    rc, se, so = run_cmd(["docker", "-v"])
    if rc:
        exit_install(f"Docker is not found", 3, se, so)
    rc, se, so = run_cmd(["docker", "ps"])
    if rc:
        exit_install(f"Docker is not running", 4, se, so)
    rc, se, so = run_cmd(["docker-compose", "-v"])
    if rc:
        exit_install(f"docker-compose is not installed", 5, se, so)
    print("ok")


def start_container_services():
    print("Starting services...", end="")
    rc, se, so = run_cmd(["docker-compose", "up", "-d"])
    if rc:
        exit_install(f"Error starting container services", 6, se, so)
    print("ok")


def run_cmd_web(cmd, **kwargs):
    return run_cmd(["docker", "exec", "hypercenter_web_1"] + cmd, **kwargs)


def check_web_status_from_container(timeout):
    print(f"Checking web service status from container with timeout {timeout} sec ...", end="")
    port = int(8080)
    start = time.time()
    rc, se, so = None, None, None
    while time.time() - start < timeout:
        rc, se, so = run_cmd_web(["curl", f"http://localhost:{port}"])
        if rc:
            time.sleep(10)
        else:
            break
    if rc:
        exit_install("Django web service is not running", 7, se, so)
    print("ok")


def check_web_status_from_host(port):
    print("Checking web service status from host...", end="")
    rc, se, so = run_cmd(["curl", f"http://localhost:{port}"])
    if rc:
        exit_install("Django web service is not running", 8, se, so)
    print("ok")


def run_db_migrations():
    print("Running db migrations...", end="")
    rc, se, so = run_cmd_web(["python", "manage.py", "migrate"])
    if rc:
        exit_install("Failed to apply db migrations", 9, se, so)
    print("ok")


def check_admin_url(port):
    print("Checking /admin url...", end="")
    rc, se, so = run_cmd(["curl", f"http://localhost:{port}/admin"])
    if rc:
        exit_install("Failed to access /admin url", 10, se, so)
    print("ok")


def check_search_url(port):
    print("Checking /search url...", end="")
    rc, se, so = run_cmd(["curl", f"http://localhost:{port}/"])
    if rc:
        exit_install("Failed to access /search url", 11, se, so)
    print("ok")


def check_admin_login(port, password):
    """
    <input type="hidden" name="csrfmiddlewaretoken" value="XXXXX">
    :param port:
    :param password:
    :return:
    """
    print("Checking admin login...", end="")
    url = f'http://localhost:{port}/admin/login/?next=/admin/'
    resp1 = requests.get(url)
    middlewaretoken = None
    soup = BeautifulSoup(resp1.text, 'html.parser')
    for el in soup.find_all('input'):
        if el.get('name') == 'csrfmiddlewaretoken':
            middlewaretoken = el['value']
            break
    assert middlewaretoken, "can't extract csrfmiddleware token"

    user = 'admin'
    payload = {
        'csrfmiddlewaretoken': middlewaretoken,
        "username": user,
        "password": password
    }
    resp = requests.post(url, payload, cookies=resp1.cookies)
    if not resp.ok:
        exit_install("Failed post login to admin", 12, resp.text, '')
    elif "<title>Site administration | Django site admin</title>" not in resp.text:
        exit_install("Failed to authenticate admin user", 13, resp.text, '')
    print("ok")


def check_elasticsearch_from_web_container(port):
    print("Checking elasticsearch API from django...", end="")
    rc, se, so = run_cmd_web(["curl", f"http://elasticsearch:{port}/"])
    if rc:
        exit_install("Failed to access elasticsearch API from web container", 14, se, so)
    print("ok")


def create_elasticsearch_index(port):
    print("Creating elasticsearch index...", end="")
    rc, se, so = run_cmd_web(['curl', '-s', f'elasticsearch:{port}/_cat/indices?format=json'])
    out = json.loads(so)
    if 'hypermanager' in [x['index'] for x in out]:
        print("skip")
    else:
        rc, se, so = run_cmd_web(['python', 'manage.py', 'search_index', '--create', '-f'])
        if rc:
            exit_install("Failed to create elasticsearch index", 15, se, so)
        print("ok")


def check_search_hypermanager_api(port):
    print("Checking django search api...", end="")
    resp = requests.get(f"http://localhost:{port}/search/hypermanager/")
    if not resp.ok:
        exit_install("Failed to access hypermanager api elasticsearch index", 16, resp.text, "")
    print("ok")


def check_kibana():
    print("Checking kibana is up...", end="")
    port = 5601
    rc, se, so = run_cmd(["curl", f"http://localhost:{port}/app/kibana"])
    if rc:
        exit_install("Failed to access kibana", 17, se, so)
    print("ok")


def load_sample_data(fname_json):
    print(f"Loading sample data from {fname_json}...", end="")
    rc, se, so = run_cmd_web(["python", "manage.py", "loaddata", "vcenters.json"])
    if rc:
        exit_install("Failed to load sample data", 18, se, so)
    print("ok")


def import_kibana_dashboards(space_name, import_dir):
    print("Importing kibana dashboards...", end="")
    rc, se, so = run_cmd(["python", "kibana/import_dashboards.py", space_name, import_dir])
    if rc:
        exit_install("Failed to import kibana dashboards", 19, se, so)
    print("ok")


if __name__ == "__main__":

    # install
    check_dot_env_config()
    vars = get_env_vars()
    external_port = int(vars['WEB_PORT'])
    password = vars['SUPERPASS']
    check_docker()
    #TODO check ports 8080 and 5601 are not taken
    start_container_services()
    timeout = 60
    check_web_status_from_container(timeout)
    check_web_status_from_host(external_port)
    run_db_migrations()
    check_admin_url(external_port)
    check_search_url(external_port)
    check_admin_login(external_port, password)
    check_elasticsearch_from_web_container(9200)
    create_elasticsearch_index(9200)
    check_search_hypermanager_api(external_port)
    check_kibana()

    # load sample data
    load_sample_data("vcenters.json")

    # import kibana dashboards
    import_kibana_dashboards("test", "kibana/dashboards")

    print("Done")