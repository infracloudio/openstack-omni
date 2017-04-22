# Copyright 2016 Platform9 Systems Inc.(http://www.platform9.com)
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ipaddr
from neutron.common import gceconf, gceutils
from neutron.plugins.ml2 import driver_api as api
from oslo_log import log

LOG = log.getLogger(__name__)


class GceMechanismDriver(api.MechanismDriver):
    """Ml2 Mechanism driver for GCE"""

    def __init__(self):
        super(GceMechanismDriver, self).__init__()
        self.gce_zone = gceconf.zone
        self.gce_region = gceconf.region
        self.gce_project = gceconf.project_id
        self.gce_svc_key = gceconf.service_key_path

    def initialize(self):
        LOG.info("Innitialize GCE Mechanism Driver")
        self.gce_svc = gceutils.get_gce_service(self.gce_svc_key)
        LOG.info("GCE Mechanism driver init with %s project, %s region" %
                 (self.gce_project, self.gce_region))

    def _gce_network_name(self, context):
        return 'net-' + context.current['id']

    def _gce_subnet_name(self, context):
        return 'subnet-' + context.current['id']

    def _gce_subnet_network_name(self, context):
        return 'net-' + context.current['network_id']

    @staticmethod
    def is_private_network(cidr):
        return ipaddr.IPNetwork(cidr).is_private

    def create_network_precommit(self, context):
        """Allocate resources for a new network.

        :param context: NetworkContext instance describing the new
        network.

        Create a new network, allocating resources as necessary in the
        database. Called inside transaction context on session. Call
        cannot block.  Raising an exception will result in a rollback
        of the current transaction.
        """
        LOG.info("create_network_precommit {0}".format(context.__dict__))
        pass

    def create_network_postcommit(self, context):
        """Create a network.

        :param context: NetworkContext instance describing the new
        network.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.
        """
        LOG.info("create_network_postcommit {0}".format(context.current))
        compute, project = self.gce_svc, self.gce_project
        name = self._gce_network_name(context)
        operation = gceutils.create_network(compute, project, name)
        gceutils.wait_for_operation(compute, project, operation)
        LOG.info('Created network on GCE %s' % name)

    def update_network_precommit(self, context):
        """Update resources of a network.

        :param context: NetworkContext instance describing the new
        state of the network, as well as the original state prior
        to the update_network call.

        Update values of a network, updating the associated resources
        in the database. Called inside transaction context on session.
        Raising an exception will result in rollback of the
        transaction.

        update_network_precommit is called for all changes to the
        network state. It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        LOG.info("update_network_precommit {0}".format(context.__dict__))
        pass

    def update_network_postcommit(self, context):
        """Update a network.

        :param context: NetworkContext instance describing the new
        state of the network, as well as the original state prior
        to the update_network call.

        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.

        update_network_postcommit is called for all changes to the
        network state.  It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        LOG.info("update_network_postcommit {0}".format(context.__dict__))
        pass

    def delete_network_precommit(self, context):
        """Delete resources for a network.

        :param context: NetworkContext instance describing the current
        state of the network, prior to the call to delete it.

        Delete network resources previously allocated by this
        mechanism driver for a network. Called inside transaction
        context on session. Runtime errors are not expected, but
        raising an exception will result in rollback of the
        transaction.
        """
        LOG.info("delete_network_precommit {0}".format(context.__dict__))
        pass

    def delete_network_postcommit(self, context):
        """Delete a network.

        :param context: NetworkContext instance describing the current
        state of the network, prior to the call to delete it.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Runtime errors are not
        expected, and will not prevent the resource from being
        deleted.
        """
        LOG.info("delete_network_postcommit {0}".format(context.current))
        compute, project = self.gce_svc, self.gce_project
        name = self._gce_network_name(context)
        operation = gceutils.delete_network(compute, project, name)
        gceutils.wait_for_operation(compute, project, operation)
        LOG.info('Deleted network on GCE %s' % name)

    def create_subnet_precommit(self, context):
        """Allocate resources for a new subnet.

        :param context: SubnetContext instance describing the new
        subnet.

        Create a new subnet, allocating resources as necessary in the
        database. Called inside transaction context on session. Call
        cannot block.  Raising an exception will result in a rollback
        of the current transaction.
        """
        LOG.info("create_subnet_precommit {0}".format(context.__dict__))
        pass

    def create_subnet_postcommit(self, context):
        """Create a subnet.

        :param context: SubnetContext instance describing the new
        subnet.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.
        """
        LOG.info("create_subnet_postcommit {0}".format(context.current))
        compute, project, region = self.gce_svc, self.gce_project, self.gce_region
        network_name = self._gce_subnet_network_name(context)
        name = self._gce_subnet_name(context)
        cidr = context.current['cidr']
        if self.is_private_network(cidr):
            network = gceutils.get_network(compute, project, network_name)
            network_link = network['selfLink']
            operation = gceutils.create_subnet(compute, project, region, name,
                                               cidr, network_link)
            gceutils.wait_for_operation(compute, project, operation)
            LOG.info("Created subnet %s in region %s on GCE" % (name, region))

    def update_subnet_precommit(self, context):
        """Update resources of a subnet.

        :param context: SubnetContext instance describing the new
        state of the subnet, as well as the original state prior
        to the update_subnet call.

        Update values of a subnet, updating the associated resources
        in the database. Called inside transaction context on session.
        Raising an exception will result in rollback of the
        transaction.

        update_subnet_precommit is called for all changes to the
        subnet state. It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        LOG.info("update_subnet_precommit {0}".format(context.__dict__))
        pass

    def update_subnet_postcommit(self, context):
        """Update a subnet.

        :param context: SubnetContext instance describing the new
        state of the subnet, as well as the original state prior
        to the update_subnet call.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Raising an exception will
        cause the deletion of the resource.

        update_subnet_postcommit is called for all changes to the
        subnet state.  It is up to the mechanism driver to ignore
        state or state changes that it does not know or care about.
        """
        LOG.info("update_subnet_postcommit {0}".format(context.__dict__))
        pass

    def delete_subnet_precommit(self, context):
        """Delete resources for a subnet.

        :param context: SubnetContext instance describing the current
        state of the subnet, prior to the call to delete it.

        Delete subnet resources previously allocated by this
        mechanism driver for a subnet. Called inside transaction
        context on session. Runtime errors are not expected, but
        raising an exception will result in rollback of the
        transaction.
        """
        LOG.info("delete_subnet_precommit {0}".format(context.__dict__))
        pass

    def delete_subnet_postcommit(self, context):
        """Delete a subnet.

        :param context: SubnetContext instance describing the current
        state of the subnet, prior to the call to delete it.

        Called after the transaction commits. Call can block, though
        will block the entire process so care should be taken to not
        drastically affect performance. Runtime errors are not
        expected, and will not prevent the resource from being
        deleted.
        """
        LOG.info("delete_subnet_postcommit {0}".format(context.current))
        compute, project, region = self.gce_svc, self.gce_project, self.gce_region
        cidr = context.current['cidr']
        if self.is_private_network(cidr):
            name = self._gce_subnet_name(context)
            operation = gceutils.delete_subnet(compute, project, region, name)
            gceutils.wait_for_operation(compute, project, operation)
            LOG.info("Deleted subnet %s in region %s on GCE" % (name, region))
