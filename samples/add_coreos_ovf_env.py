#!/usr/bin/env python

import atexit
import base64

from pyVim import connect
from pyVmomi import vim
from tools import cli, tasks


def setup_args():
    """
    Adds additional args to allow the vm uuid to
    be set.
    """
    parser = cli.build_arg_parser()
    parser.add_argument('--vm-name', help="Name of the virtual machine.")
    parser.add_argument('--ignition-config', help="Path to ignition config.")
    return cli.prompt_for_password(parser.parse_args())

def get_obj(content, vim_type, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vim_type, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def add_ovf_env(host, user, password, port, vm_name, ignition_config, **kwargs):
    si = connect.SmartConnectNoSSL(
        host=host, user=user, pwd=password, port=int(port))
    atexit.register(connect.Disconnect, si)

    content = si.RetrieveContent()
    vm = get_obj(content, [vim.VirtualMachine], vm_name)

    spec = vim.vm.ConfigSpec()
    opt = vim.option.OptionValue()
    opt.key = "guestinfo.ovfenv"
    opt.value = '<Environment oe:id="" xmlns="http://schemas.dmtf.org/ovf/environment/1" xmlns:oe="https://schemas.dmtf.org/ovf/environment/1" xmlns:xml="http://www.w3.org/XML/1998/namespace" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><PropertySection><Property oe:key="guestinfo.coreos.config.data" oe:value="{0}"/><Property oe:key="guestinfo.coreos.config.data.encoding" oe:value="base64"/></PropertySection></Environment>'.format(base64.b64encode(open(ignition_config).read()))
    spec.extraConfig = [opt]
    task = vm.ReconfigVM_Task(spec)
    tasks.wait_for_tasks(si, [task])

if __name__ == "__main__":
    add_ovf_env(**setup_args().__dict__)
