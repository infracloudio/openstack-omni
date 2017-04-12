import hashlib
import os
import sys
import uuid

import gceutils
from glanceclient import Client
from keystoneauth1 import loading, session


def get_glance_client(version='2',
                      auth_url=os.environ['OS_AUTH_URL'],
                      project_name=os.environ['OS_PROJECT_NAME'],
                      project_domain_name=os.environ['OS_PROJECT_DOMAIN_NAME'],
                      username=os.environ['OS_USERNAME'],
                      user_domain_name=os.environ['OS_USER_DOMAIN_NAME'],
                      password=os.environ['OS_PASSWORD']):

    loader = loading.get_plugin_loader('password')
    auth = loader.load_from_options(
        auth_url=auth_url,
        project_name=project_name,
        project_domain_name=project_domain_name,
        username=username,
        user_domain_name=user_domain_name,
        password=password)
    sess = session.Session(auth=auth)
    return Client('2', session=sess)


class GcpImages(object):
    GC_PUBLIC_PROJECTS = [
        'cos-cloud', 'centos-cloud', 'debian-cloud', 'rhel-cloud',
        'suse-cloud', 'ubuntu-os-cloud', 'windows-cloud'
    ]

    GC_PUBLIC_PROJECTS = [
        'debian-cloud',
    ]

    def __init__(self, service_key_path):
        self.gce_svc = gceutils.get_gce_service(service_key_path)
        self.glance_client = get_glance_client()
        self.img_kind = {
            'RAW': 'ami',
        }

    def register_images(self):
        for image in self.get_all_public_images():
            self.glance_image_register(self.convert_gce_to_glance(image))

    def glance_image_register(self, image):
        x = self.glance_client.images.create(**image)
        print(x)
        self.glance_client.images.add_location(image['id'],
                                           url='gce://%s' % (image['gce_link'], ),
                                           metadata={'spam': 'ham'})
        print(image['name'])

    def get_all_public_images(self):
        images = []
        for project in self.GC_PUBLIC_PROJECTS:
            images.extend(gceutils.get_images(self.gce_svc, project))
        return images

    def _get_image_uuid(self, gce_id):
        md = hashlib.md5()
        md.update(gce_id)
        return str(uuid.UUID(bytes=md.digest()))

    def convert_gce_to_glance(self, gce_img_data):
        return {
            'id': self._get_image_uuid(gce_img_data['id']),
            'name': gce_img_data['name'],
            'container_format': self.img_kind[gce_img_data['sourceType']],
            'disk_format': self.img_kind[gce_img_data['sourceType']],
            'visibility': 'public',
            'pf9_description': gce_img_data['description'],
            'gce_id': gce_img_data['id'],
            'gce_size': gce_img_data['diskSizeGb'],
            'gce_link': gce_img_data['selfLink']
        }


if __name__ == '__main__':
    gcp_images = GcpImages(sys.argv[1])
    gcp_images.register_images()
