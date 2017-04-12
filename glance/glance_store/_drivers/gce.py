# Copyright (c) 2016 Platform9 Systems Inc. (http://www.platform9.com)
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

import logging

import gceutils
import glance_store.driver
import glance_store.location
from glance_store import capabilities, exceptions
from glance_store.i18n import _
from oslo_config import cfg
from six.moves import urllib

LOG = logging.getLogger(__name__)

MAX_REDIRECTS = 5
STORE_SCHEME = 'gce'

gce_group = cfg.OptGroup(
    name='GCE', title='Options to connect to an Google cloud')

gce_opts = [
    cfg.StrOpt(
        'service_key_path', help='Service key of GCE account', secret=True),
    cfg.StrOpt('zone', help='GCE region'),
    cfg.StrOpt('project_id', help='GCE project id'),
]

# CONF.register_group(gce_group)
# CONF.register_opts(gce_opts, group=gce_group)


class StoreLocation(glance_store.location.StoreLocation):
    """Class describing an GCE URI."""

    def __init__(self, store_specs, conf):
        super(StoreLocation, self).__init__(store_specs, conf)

    def process_specs(self):
        LOG.info('process specs')
        self.scheme = self.specs.get('scheme', STORE_SCHEME)
        self.gce_id = self.specs.get('gce_id')

    def get_uri(self):
        LOG.info('get uri')
        return "{}://{}".format(self.scheme, self.gce_id)

    def parse_uri(self, uri):
        """
        Parse URLs. This method fixes an issue where credentials specified
        in the URL are interpreted differently in Python 2.6.1+ than prior
        versions of Python.
        """
        LOG.info('parse uri %s' % (uri, ))
        if not uri.startswith('%s://' % STORE_SCHEME):
            reason = (_("URI %(uri)s must start with %(scheme)s://") % {
                'uri': uri,
                'scheme': STORE_SCHEME
            })
            LOG.info(reason)
            raise exceptions.BadStoreUri(message=reason)
        pieces = urllib.parse.urlparse(uri)
        self.scheme = pieces.scheme
        gce_id = pieces.netloc + '/' + pieces.path
        if pieces.path == '':
            LOG.info(_("No image gce_id specified in URL"))
            raise exceptions.BadStoreUri(uri=uri)
        self.gce_id = gce_id


class Store(glance_store.driver.Store):
    """An implementation of the HTTP(S) Backend Adapter"""

    _CAPABILITIES = (capabilities.BitMasks.RW_ACCESS |
                     capabilities.BitMasks.DRIVER_REUSABLE)

    def __init__(self, conf):
        super(Store, self).__init__(conf)
        conf.register_group(gce_group)
        conf.register_opts(gce_opts, group=gce_group)
        self.gce_zone = conf.GCE.zone
        self.gce_project = conf.GCE.project_id
        self.gce_svc_key = conf.GCE.service_key_path
        self.gce_svc = gceutils.get_gce_service(self.gce_svc_key)
        LOG.info('Innitialize Glance Store driver')

    def get_schemes(self):
        """
        :retval tuple: containing valid scheme names to
                associate with this store driver
        """
        LOG.info('get schemes')
        return ('gce', )

    @capabilities.check
    def get(self, location, offset=0, chunk_size=None, context=None):
        """
        Takes a `glance_store.location.Location` object that indicates
        where to find the image file, and returns a tuple of generator
        (for reading the image file) and image_size

        :param location `glance_store.location.Location` object, supplied
                        from glance_store.location.get_location_from_uri()
        """
        LOG.info('get on store')
        yield ('gce://generic', self.get_size(location, context))

    @capabilities.check
    def delete(self, location, context=None):
        """Takes a `glance_store.location.Location` object that indicates
        where to find the image file to delete

        :param location: `glance_store.location.Location` object, supplied
                  from glance_store.location.get_location_from_uri()
        :raises NotFound if image does not exist
        """
        LOG.info("Delete image")
        gce_id = location.get_store_uri()
        LOG.info(gce_id)
        # TODO: Complete

    def get_size(self, location, context=None):
        """
        Takes a `glance_store.location.Location` object that indicates
        where to find the image file, and returns the size

        :param location `glance_store.location.Location` object, supplied
                        from glance_store.location.get_location_from_uri()
        :retval int: size of image file in bytes
        """
        LOG.info("Get image size")
        gce_id = location.get_store_uri()
        LOG.inf(gce_id)
        # TODO: Actual size
        return 10
