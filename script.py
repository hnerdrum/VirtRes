# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Connect to an OpenStack cloud.

For a full guide see
https://docs.openstack.org/openstacksdk/latest/user/guides/connect_from_config.html
"""

import argparse
import os

import openstack
from openstack.config import loader
import sys

# FUNCTION USED IN DEPLOYMENT, SOME OF WHICH ARE FOR TESTING/LISTING


def create_connection(auth_url, region, project_name, username, password):

    return openstack.connect(
        auth_url=auth_url,
        project_name=project_name,
        username=username,
        password=password,
        region_name=region,
        domain_name="insat"
    )

def list_servers(conn):
    print("List Servers:")

    for server in conn.compute.servers():
        print(server)

def list_images(conn):
    print("List Images")

    for image in conn.compute.images():
        print(image.name)

def list_flavors(conn):
    print("List Flavors")

    for flavor in conn.compute.flavors():
        print(flavor.name)

def list_networks(conn):
    print("List Networks:")

    for network in conn.network.networks():
        print(network.name, " - ", network.id, " - ", network.subnet_ids)

def list_routers(conn):
    print("List Routers")

    for router in conn.network.routers():
        print(router)

def create_network(conn, nwName, subnetName, mask, gw):
    print("Create Network:")

    example_network = conn.network.create_network(
        name=nwName)

    print(example_network)

    example_subnet = conn.network.create_subnet(
        name=subnetName,
        network_id=example_network.id,
        ip_version='4',
        cidr=mask,
        gateway_ip=gw)

    print(example_subnet)

def create_server(conn, SERVER_NAME, IMAGE_NAME, FLAVOR_NAME, NETWORK_NAME, KEYPAIR_NAME):
    print("Create Server:")

    image = conn.compute.find_image(IMAGE_NAME)
    flavor = conn.compute.find_flavor(FLAVOR_NAME)
    network = conn.network.find_network(NETWORK_NAME)

    server = conn.compute.create_server(
        name=SERVER_NAME, image_id=image.id, flavor_id=flavor.id,
        networks=[{"uuid": network.id}])

    server = conn.compute.wait_for_server(server)


def create_router(**router_body):
    print("Create router:")

    conn.network.create_router(*router_body)

def add_interface(router, subnet):
    print("Add interface to router: ", router, " - subnet: ", subnet)

    rt = conn.network.add_interface_to_router(router, subnet)

    print(rt)

# VARIABLES USED IN DEPLOYMENT

# Subnet-ids to create interfaces between routers and networks
public_network_id = "577d76a8-31b0-4e12-a8da-93748f1b3459"
public_subnet = "369ab09c-411c-49a4-98f7-2b807a4b77df"
net21_subnet = "2875ff9f-283f-4d40-91c1-bfdee9afc528"
net22_subnet = "42cced10-871d-46ef-b303-b71bf876c5d1"

# Creating the two networks necessary
# Could have used a function to get these dynamically from user, but hardcoded for simplicity
gw21 = "192.168.3.1"
gw22 = "192.168.4.1"


# Parameters used to create routers with custom names
# Could have used a function to get these dynamically from user, but hardcoded for simplicity
router21_body = {
    'name': "RT21",
}
router22_body = {
    'name': "RT22"
}

# DEPLOYMENT FUNCTION CALLS

# Connecting to OpenStack
conn = create_connection("https://os-api-ext.insa-toulouse.fr:5000/v3", "RegionINSA", "5SDBD-Virt-B1-5", "hnerdrum", "Yivx$G7")

# Our two networks
net21 = create_network(conn, "Net21", "subnet21", "192.168.3.0/24", gw21)
net22 = create_network(conn, "Net22", "subnet22", "192.168.4.0/24", gw22)

# Creating VMs necessary for the service
calc = create_server(conn, "Calc2", "alpine-node_CalcService", "nano", "Net21", "calcKeyPair")
div = create_server(conn, "Div2", "alpine-node_DivService", "nano", "Net22", "divKeyPair")
mul = create_server(conn, "Mul2", "alpine-node_MulService", "nano", "Net22", "mulKeyPair")
sub = create_server(conn, "Sub2", "alpine-node_SubService", "nano", "Net22", "subKeyPair")
sum = create_server(conn, "Sum2", "alpine-node_SumService", "nano", "Net22", "sumKeyPair")

# The routers acting our virtual networks and between public network and our virtual networks
rt21 = create_router(**router21_body)
rt22 = create_router(**router22_body)

# Creating the proper interfaces according to wanted topology
add_interface(rt21, public_subnet)
add_interface(rt21, net21_subnet)
add_interface(rt22, net21_subnet)
add_interface(rt22, net22_subnet)
