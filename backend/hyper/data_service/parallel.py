from concurrent.futures import ThreadPoolExecutor
import time
import random
import subprocess
# from common import run_cmd


def squared(n):
    print("Processing {}".format(n))
    time.sleep(n)
    print("Done processing {}".format(n))
    return n**2


def run_parallel(func_list, *args_list):
    njobs = len(func_list)
    assert njobs >= 1, "func_list should be more or one"
    print("Starting ThreadPoolExecutor with {} threads".format(njobs))
    results = []
    with ThreadPoolExecutor(max_workers=njobs) as executor:
        futures = []
        for i, func in enumerate(func_list):
            if args_list:
                future = executor.submit(func, *args_list[i], )
            else:
                future = executor.submit(func, )
            futures.append(future)

        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                print(e)
                results.append(None)

    print("All tasks complete")
    return results


def ping_host(host):
    print("Pinging host {}".format(host))
    try:
        subprocess.check_call(['ping', '-c', '5', host])
        return True
    except Exception as e:
        print(e)
        return False


def parallel_ping(hosts):
    n = len(hosts)
    func_list = [globals()['ping_host']] * n
    args_list = []
    for host in hosts:
        args_list.append((host,))
    pings = run_parallel(func_list, *args_list)
    res = dict()
    for host, p in zip(hosts, pings):
        res[host] = p
    return res


def ping_host_timeout(host, timeout):
    print("Pinging host {} with timeout {}".format(host, timeout))
    try:
        subprocess.check_call(['ping', '-c', str(timeout), host])
        return True
    except Exception as e:
        print(e)
        return False


def parallel_two_args(hosts, timeouts):
    n = len(hosts)
    func_list = [globals()['ping_host_timeout']] * n
    args_list = []
    for host, timeout in zip(hosts, timeouts):
        args_list.append((host, timeout))
    pings = run_parallel(func_list, *args_list)
    res = dict()
    for host, p in zip(hosts, pings):
        res[host] = p
    return res


def no_args():
    print("executing no_args")


if __name__ == '__main__':
    # no args
    func_list = [globals()['no_args']] * 2
    res = run_parallel(func_list, )
    print(res)

    # one argument
    func_list = [globals()['squared']] * 10
    args_list = []
    for i in range(len(func_list)):
        n = random.randint(1, 5)
        args_list.append((n, ))
    res = run_parallel(func_list, *args_list)
    print("Numbers", args_list)
    print("Results", res)

    # one argument
    hosts = [
        "host1",
        "host2"
    ]
    print(parallel_ping(hosts))

    # two arguments
    hosts = [
        "host1",
        "host2"
    ]
    timeouts = [1, 2]
    print(parallel_two_args(hosts, timeouts))
