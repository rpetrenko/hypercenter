import subprocess
import os
import sys
import json
from urllib.parse import urlparse

DEBUG = True


def print_json(obj, indent=2):
    print(json.dumps(obj, indent=indent))


def clean_url(url):
    res = urlparse(url)
    return "{}://{}".format(res.scheme, res.netloc)


def run_cmd(cmd_parts, decode=True, verbose=False, env=None, timeout=None):
    """
    Execute shell commands locally
    :param cmd_parts:
    :param decode:
    :param verbose:
    :param env:
    :return:
    """
    if DEBUG:
        # print("env", env)
        print("CMD:", " ".join(cmd_parts))
    if env is not None:
        env.update(os.environ)
    res = subprocess.Popen(cmd_parts,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
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
        print("CMD", cmd_parts)
        print("rc:", rc)
        print("se:", se)
        print("so:", so)
    return rc, se, so


def govc(args, format=None, env=None, verbose=False, timeout=None):
    if format == 'json':
        args.insert(1, '-json')
    cmd = ["govc"] + args
    rc, se, so = run_cmd(cmd, env=env, verbose=verbose, timeout=timeout)
    if not rc and format == 'json':
        try:
            so = json.loads(so)
        except Exception as e:
            print(env)
            print(cmd)
            print(so)
            print(e)
    return rc, se, so


def parse_tab_list_view(lines, key='Name', sep=":"):
    """

    :param lines:
    :param key:
    :return: list of dictionaries
    """
    res = list()
    temp = dict()
    if isinstance(lines, str):
        lines = lines.splitlines()
    for line in lines:
        if not line:
            continue
        sep_pos = line.find(sep)
        if sep_pos == -1:
            raise Exception("separator is not found on the output line")
        k = line[:sep_pos]
        v = line[sep_pos+1:]
        k = k.strip()
        v = v.strip()
        if line.startswith(key):
            if temp:
                res.append(temp)
                temp = dict()
        temp[k] = v
    res.append(temp)
    return res


def _generate_indeces_from_options(opts):
    """
    list of indeces, this method will support index ranges
    :param opts:
    :return:
    """
    res = []
    for opt in opts:
        if "-" in opt:
            start, end = opt.split('-')
            res.extend(range(int(start), int(end) + 1))
        else:
            res.append(int(opt))
    return res


def generate_obj_ids(arg_ids, obj):
    obj_ids = sorted([o.pk for o in obj.objects.all()])
    if arg_ids != '':
        temp_ids = _generate_indeces_from_options(arg_ids)
        obj_ids = [x for x in temp_ids if x in obj_ids]
    print(" ".join([str(i) for i in obj_ids]))
    return obj_ids


if __name__ == "__main__":

    fname = sys.argv[1]
    assert fname
    # test ls
    cmd_parts = ['ls', '-l', '.']
    rc, se, so = run_cmd(cmd_parts)
    print(rc, se, so)

    # test env
    env = json.load(open(fname, 'r'))
    rc, se, so = govc(['about'], env=env, format='json')
    print(f"rc={rc}")
    print(f"se={se}")
    print(json.dumps(so, indent=2))
