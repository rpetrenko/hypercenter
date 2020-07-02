import sys
import datetime as dt
import json
from hyper.data_service.common import clean_url, govc, parse_tab_list_view, print_json


def get_vcenter_from_config(config_json):
    vcenter_url = "https://{}".format(config_json['vcenter']['host'])
    vcenter = HypervisorVcenter(
        vcenter_url,
        config_json['vcenter']['username'],
        config_json['vcenter']['password']
    )
    return vcenter


class HypervisorVcenter(object):

    def __init__(self, url, username, password):
        url = clean_url(url)
        self.url = url
        self.username = username
        self.password = password
        self.env = self._set_env_vars()

    def _set_env_vars(self):
        env = {
            "GOVC_URL": self.url,
            "GOVC_USERNAME": self.username,
            "GOVC_PASSWORD": self.password,
            "GOVC_INSECURE": "true"
        }
        return env

    def _run_govc(self, args, format='json', verbose=False, timeout=None):
        res = govc(args, env=self.env, format=format, verbose=verbose, timeout=timeout)
        return res

    def _check_output(self, rc, se, so):
        if not rc and not se:
            return so
        else:
            raise Exception(so)

    def _get_host_paths(self):
        rc, se, so = self._run_govc(["find", "-type", "h"])
        return self._check_output(rc, se, so)

    def _get_host_info(self, host_path):
        rc, se, so = self._run_govc(['host.info', host_path], format='')
        return self._check_output(rc, se, so)

    def about(self):
        so = self._check_output(*self._run_govc(['about']))
        return so['About']

    def get_version(self):
        rc, se, so = self._run_govc(['about'])
        return self._check_output(rc, se, so)["About"]["Version"]

    def get_datacenters(self, short=True):
        if short:
            format = None
        else:
            format = 'json'
        rc, se, so = self._run_govc(["datacenter.info"], format=format)
        try:
            out = self._check_output(rc, se, so)
            if short:
                out = parse_tab_list_view(out)
            return out
        except Exception as e:
            print(e)
            return []

    def get_hosts(self, name=None):
        host_paths = self._get_host_paths()
        res = list()
        for host_path in host_paths:
            host_info = self._get_host_info(host_path)
            host_structure = parse_tab_list_view(host_info)[0]
            if name is not None and name == host_structure["Name"]:
                res.append(host_structure)
                break
            else:
                res.append(host_structure)
        return res

    def get_host(self, dc, host):
        """
        govc host.info -json -dc <datacenter> -host <hostname>
        :param dc:
        :param host:
        :return:
        """
        rc, se, so = self._run_govc(['host.info', '-dc', dc, '-host', host])
        if so.get('HostSystems'):
            return so['HostSystems'][0]
        return None

    def _get_datastores_path(self):
        rc, se, so = self._run_govc(["find", "-type", "s"])
        return self._check_output(rc, se, so)

    def get_hosts_in_datacenter(self, dc):
        rc, se, so = self._run_govc(['find', '-type', 'h', '-dc', dc])
        return so

    def get_datastore_info(self, dc, ds):
        """
         govc datastore.info -json -dc <datacenter> <datastore>
        :param dc:
        :param ds:
        :return:
        """
        rc, se, so = self._run_govc(['datastore.info', '-dc', dc, ds])
        return so['Datastores'][0]

    def get_datastore(self, datacenter, ds_name):
        ds_paths = self._get_datastores_path()
        ds_search_path = "{}/datastore/{}".format(datacenter, ds_name)
        for ds_path in ds_paths:
            if ds_search_path == ds_path:
                rc, se, so = self._run_govc(["datastore.info", '-dc', datacenter], format='json')
                out = self._check_output(rc, se, so)
                return out['Datastores']
        return None

    def get_datastores(self, host_path):
        host = host_path.split('/')[-1]
        dc = host_path.split('/')[1]
        rc, se, so = self._run_govc(["host.info", '-dc', dc, "-host.dns", host], format='json')
        try:
            out = self._check_output(rc, se, so)
        except Exception as e:
            print("GOVCERR: {}".format(e))
            return []
        config = out['HostSystems'][0]['Config']
        if not config:
            raise Exception("no config found for host_path {}".format(host_path))
        tmp = [x['Volume'] for x in config['FileSystemVolume']['MountInfo'] if x['Volume']['Name']]
        res = []
        for t in tmp:
            ds_type = t["Type"]
            ds_structure = {
                "ds_type": ds_type,
                "name": t["Name"],
                "capacity": t["Capacity"]
            }
            if ds_type == "VMFS":
                ds_structure["uuid"] = t["Uuid"]
                ds_structure["version"] = t["Version"]
                ds_structure["devices"] = []
                if t.get("Extent"):
                    ds_structure["devices"] = [{"name": x["DiskName"], "partition": x["Partition"]} for x in t["Extent"]]
            elif ds_type.startswith("NFS"):
                ds_structure["remotehost"] = t["RemoteHost"]
                ds_structure["remotepath"] = t["RemotePath"]
            elif ds_type == "VVOL":
                ds_structure["scid"] = t["ScId"]
                ds_structure["array"] = t["StorageArray"][0]["Name"]
            else:
                print("GOVCERR: unsupported datastore type {}".format(ds_type))
                continue
            res.append(ds_structure)
        return res

    def list_vms(self, datacenter):
        """
        replace slow command:
            govc find /<datacenter>/vm -type m
        with ls:
            govc ls /<datacenter>/vm/*
        :param datacenter:
        :return: list of the VM-paths
        """
        rc, se, so = self._run_govc(['ls', '/{}/vm/*'.format(datacenter)],
                                    format='', verbose=False)
        out = self._check_output(rc, se, so)
        if out:
            return out.splitlines()
        else:
            return []

    def vm_info_path(self, vm_path, format=''):
        """
        govc vm.info /<datacenter>/vm/<vm-name>
        :param vm_path:
        :return:
        """
        rc, se, so = self._run_govc(['vm.info', vm_path], format=format)
        return so

    def vm_info(self, dc, vm_name):
        """
        govc vm.info -dc <datacenter> -json <vmname>
        :param dc:
        :param vm_name:
        :return:
        """
        rc, se, so = self._run_govc(['vm.info', '-dc', dc, vm_name])
        return so['VirtualMachines']

    def vm_get_device_by_label(self, dc, vm_name, device_label):
        res = self.vm_info(dc, vm_name)
        for device in res[0]['Config']['Hardware']['Device']:
            if device['DeviceInfo']['Label'] == device_label:
                return device
        return None

    def vm_get_storage_device_backing(self, dc, vm_name):
        res = self.vm_info(dc, vm_name)
        backing_devices = []
        for device in res[0]['Config']['Hardware']['Device']:
            if device.get('Backing') and device['Backing'].get('Datastore'):
                backing_devices.append(device)
        return backing_devices

    def get_serial_filename_map(self, serials, dc, vmname):
        """
        Given list of serial numbers, return dictionary with them mapped
        to a filename path of a backing device
        :param serials:
        :param dc:
        :param vmname:
        :return:
        """
        backing_devices = self.vm_get_storage_device_backing(dc, vmname)
        serial_filename_map = {}
        for serial in serials:
            fname = None
            # filter out serials that have already been used
            for device in backing_devices:
                if device['Backing'].get('DeviceName') and serial.lower() in device['Backing']['DeviceName']:
                    fname = device['Backing']['FileName']
                    break
            serial_filename_map[serial] = fname
        return serial_filename_map

    def vm_connection_state(self, dc, vm_name):
        res = self.vm_info(dc, vm_name)
        if res is None:
            return res
        return [x['Runtime']['ConnectionState'] for x in res]

    def get_datastore_names(self, host):
        dcs = self.get_datastores(host)
        res = [x["Name"] for x in dcs]
        return res

    def get_datastore_count(self, host):
        paths = self._get_host_paths()
        for path in paths:
            host_from_path = path.split('/')[-1]
            dc = path.split('/')[1]
            if host == host_from_path:
                break
        rc, se, so = self._run_govc(["host.info", '-dc', dc, "-host.dns", host], format='json')
        out = self._check_output(rc, se, so)['HostSystems'][0]['Config']['FileSystemVolume']['MountInfo']
        return len(out)

    def get_datastore_counts(self):
        res = []
        hosts = self.get_hosts()
        for host in hosts:
            temp_res = {}
            temp_res['hostname'] = host['Name']
            temp_res['datastore_count'] = self.get_datastore_count(host['Name'])
            res.append(temp_res)
        return res

    def get_lun_count(self, host):
        paths = self._get_host_paths()
        for path in paths:
            host_from_path = path.split('/')[-1]
            dc = path.split('/')[1]
            if host == host_from_path:
                break
        # govc host.esxcli -json  -dc=datacenter -host=hostname storage core device list | jq
        rc, se, so = self._run_govc(["host.esxcli", '-dc', dc, "-host.dns", host, 'storage', 'core', 'device', 'list'], format='json')
        out = self._check_output(rc, se, so)
        return len(out)

    def get_lun_counts(self):
        res = []
        hosts = self.get_hosts()
        for host in hosts:
            temp_res = {}
            temp_res['hostname'] = host['Name']
            temp_res['datastore_count'] = self.get_datastore_count(host['Name'])
            temp_res['reachable'] = True
            try:
                temp_res['lun_count'] = self.get_lun_count(host['Name'])
            except Exception as err:
                print(err)
                temp_res['lun_count'] = 0
                temp_res['reachable'] = False
            res.append(temp_res)
        return res

    def get_recent_tasks(self, limit=25):
        """
        $ govc tasks
        """
        rc, se, so = self._run_govc(['tasks', '-n', str(limit)], format='')
        return so

    def get_host_date(self, datacenter, host):
        """
        $ govc host.date.info -dc <datacenter> -host <hostname> -json

        For datetime format used by pyvmomi, check here
        https://github.com/vmware/pyvmomi/blob/master/pyVmomi/Iso8601.py

        :param datacenter:
        :param host:
        :return: '2020-02-14T19:21:26.919511Z'
        """
        rc, se, so = self._run_govc(['host.date.info', '-dc', datacenter, '-host', host])
        so = self._check_output(rc, se, so)
        date_time_str = so['Current']
        date_time_obj = dt.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        return date_time_obj

    def get_vm_info(self, datacenter, vm):
        cmd_parts = ['vm.info', '-dc', datacenter, vm]
        rc, se, so = self._run_govc(cmd_parts, format='')
        return so

    def get_host_for_vm(self, datacenter, vm):
        vm_info = self.get_vm_info(datacenter, vm)
        host = None
        if not vm_info:
            return host
        for line in vm_info.split('\n'):
            line = line.strip()
            if line and line[:5] == "Host:":
                host = line.split()[-1].strip()
        return host

    def get_disk_info(self, datacenter, host):
        """
        govc host.storage.info -dc <datacenter> -host <hostname>
        :param datacenter:
        :param host:
        :return:
        """
        cmd_parts = ['host.storage.info', '-dc', datacenter, '-host', host]
        rc, se, so = self._run_govc(cmd_parts, format='json')
        res = list()
        if so:
            for disk in so['StorageDeviceInfo']['ScsiLun']:
                res.append({
                    'CanonicalName': disk['CanonicalName'],
                    'Vendor': disk['Vendor'].strip(),
                    'DevicePath': disk['DevicePath'],
                    'LocalDisk': disk['LocalDisk'],
                    'Model': disk['Model'].strip(),
                    'Capacity': disk['Capacity']
                })
        return res


if __name__ == "__main__":

    fname = sys.argv[1]
    assert fname
    govc_vars = json.load(open(fname, 'r'))
    vcenter = HypervisorVcenter(
        govc_vars["GOVC_URL"],
        govc_vars["GOVC_USERNAME"],
        govc_vars["GOVC_PASSWORD"]
    )

    print("TEST 1: check online")
    print_json(vcenter.about())
    print(vcenter.get_version())

    print("TEST 2: get hosts")
    hosts = vcenter.get_hosts()

    for i, host in enumerate(hosts[:1]):
        if host['State'] == 'notResponding':
            print("ERROR: host not responding {}".format(host["Path"]))
        else:
            print("host")
            print_json(host)
            print("Datastores for hostpath {}, vcenter {}".format(host['Path'], vcenter.url))
            datastores = vcenter.get_datastores(host['Path'])
            print_json(datastores)
        print("==================done {} ==============".format(i))



