import pprint
from hyper.data_service.govc_wrapper import HypervisorVcenter
from hyper.models import HyperManager
DEBUG = False


def get_hv_from_db(obj_id):
    obj = HyperManager.objects.get(pk=obj_id)
    print("got hyper manager: {}".format(obj))
    return obj


def create_hv_from_obj(obj):
    url = obj.url
    username = obj.username
    password = obj.password
    hv = HypervisorVcenter(url, username=username, password=password)
    return hv


def update_online_status(obj_id):
    obj = get_hv_from_db(obj_id)
    hv = create_hv_from_obj(obj)
    version = hv.get_version()
    online = version is not None
    print("Vcenter {}, version {}, online {}".format(hv.url, version, online))
    obj.update_status(online)
    obj.version = version
    obj.save()
    return obj


def get_hosts_from_db(hv_obj):
    return Host.objects.filter(hypervisor=hv_obj)


def get_host_from_db(host_id):
    return Host.objects.get(pk=host_id)


def get_host_detail_from_db(obj_id):
    return HostDetail.objects.get(pk=obj_id)


def get_device_from_db(name):
    try:
        return Device.objects.get(name=name)
    except Device.DoesNotExist:
        return None


def get_hv_for_host_db(host_name):
    return Hypervisor.objects.filter(host__name=host_name).first()


def update_host_detail(host_struct):
    # create/update host detail
    name = host_struct['Name']
    hostpath = host_struct['Path']
    kwargs = {
        "name": name,
        "hostpath": hostpath,
        "manufacture": host_struct['Manufacturer'],
        "logicalcpu": host_struct['Logical CPUs'],
        "processor": host_struct['Processor type'],
        "cpuusage": host_struct['CPU usage'],
        "memory": host_struct['Memory'],
        "memoryusage": host_struct['Memory usage'],
        "boottime": host_struct['Boot time'],
        "state": host_struct['State']
    }
    obj = HostDetail.objects.filter(name=name, hostpath=hostpath).first()
    if not obj:
        print("Creating new host detail for host {}".format(name))
        obj = HostDetail.objects.create(**kwargs)
    else:
        print("Updating host detail for host {}".format(name))
        obj.__dict__.update(kwargs)
    obj.save()
    return obj.id


def update_host(name, hv_obj, host_detail_obj):

    # create/update host
    kwargs = {
        "name": name,
        "hypervisor": hv_obj,
        "detail": host_detail_obj
    }
    obj = Host.objects.filter(hypervisor=hv_obj, name=name).first()
    if not obj:
        print("Creating new host {} for vc {}".format(name, hv_obj.name))
        obj = Host.objects.create(**kwargs)
    else:
        print("Updating host {} for vc {}".format(name, hv_obj.name))
        obj.__dict__.update(kwargs)
    obj.save()
    host_id = obj.id
    print(host_id)


def update_device(ds_obj, device_struct):
    print("Creating/updating {} for {}".format(device_struct, ds_obj))
    name = device_struct['name']
    partition = device_struct['partition']
    # obj = ds_obj.devices.filter(name=name, partition=partition).first()
    # device path and partition number should be unique
    # that's why we are searching globally on all existing devices
    obj = Device.objects.filter(name=name, partition=partition).first()
    if not obj:
        obj = Device.objects.create(**device_struct)
        obj.save()
        obj_id = obj.id
        print("created VMFS backing device {}".format(obj_id))
        ds_obj.devices.add(obj)
        ds_obj.save()
    else:
        obj.__dict__.update(device_struct)
        obj.save()
        obj_id = obj.id
        print("updated backing device {}".format(obj_id))


def update_datastore(host_obj, ds_struct):
    name = ds_struct['name']
    ds_type = [a for a, b in Datastore.CHOICES if b == ds_struct["ds_type"]][0]
    kwargs = {
        "name": name,
        "ds_type": ds_type,
        "capacity": ds_struct['capacity']
    }
    if ds_type == Datastore.VMFS:
        kwargs.update({
            'uuid': ds_struct['uuid'],
            'version': ds_struct['version']
        })
    elif ds_type == Datastore.NFS or ds_type == Datastore.NFS41:
        kwargs.update({
            'remotehost': ds_struct['remotehost'],
            'remotepath': ds_struct['remotepath']
        })
    elif ds_type == Datastore.VVOL:
        kwargs.update({
            'scid': ds_struct['scid'],
            'array': ds_struct['array']
        })
    if DEBUG:
        pprint.pprint(kwargs)
    if ds_type == Datastore.VMFS:
        # since VMFS can be mounted to multiple hosts, search globally
        ds_obj = Datastore.objects.filter(uuid=ds_struct['uuid']).first()
    elif ds_type == Datastore.NFS or ds_type == Datastore.NFS41:
        # same for nfs, no need to have multiple objects for the same nfs share
        ds_obj = Datastore.objects.filter(remotehost=ds_struct['remotehost'], remotepath=ds_struct['remotepath']).first()
    else:
        ds_obj = host_obj.datastores.filter(name=name).first()

    if not ds_obj:
        print("Creating new datastore {} for host {}".format(name, host_obj.name))
        ds_obj = Datastore.objects.create(**kwargs)
        ds_obj.save()
        print("adding new datastore {} to host {}".format(ds_obj.id, host_obj.id))
        host_obj.datastores.add(ds_obj)
        host_obj.save()
    else:
        print("Updating existing datastore {} for host {}".format(name, host_obj.name))
        ds_obj.__dict__.update(kwargs)
        ds_obj.save()
        obj_id = ds_obj.id
        print("updated datastore {}".format(obj_id))

    # handle devices for VMFS
    if ds_type == Datastore.VMFS:
        for device_struct in ds_struct['devices']:
            update_device(ds_obj, device_struct)
