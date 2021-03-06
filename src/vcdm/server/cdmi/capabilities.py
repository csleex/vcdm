##
# Copyright 2002-2012 Ilja Livenson, PDC KTH
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##
from httplib import OK

try:
    import json
except ImportError:
    import simplejson as json

from vcdm.server.cdmi.cdmi_content_types import CDMI_CAPABILITY
from vcdm.server.cdmi.generic import CDMI_VERSION, parse_path, get_common_body
from vcdm.server.cdmi import current_capabilities
from vcdm.server.cdmi.cdmiresource import StorageResource


capability_objects = {'system': current_capabilities.system,
                      'dataobject': current_capabilities.dataobject,
                      'mq': current_capabilities.mq,
                      'container': current_capabilities.container}


class Capability(StorageResource):
    isLeaf = True

    def render_GET(self, request):
        # for now only support top-level capabilities
        _, __, fullpath = parse_path(request.path)

        body = get_common_body(request, None, fullpath)
        # is it request for a system-level capability?
        if fullpath == '/cdmi_capabilities':
            body['capabilities'] = capability_objects['system']
            body.update({
                    'childrenrange': "0-2",
                    'children': [
                            "dataobject/",
                            "container/",
                        ]
                })
        elif fullpath.startswith('/cdmi_capabilities/dataobject'):
            body['capabilities'] = capability_objects['dataobject']
        elif fullpath.startswith('/cdmi_capabilities/container'):
            body['capabilities'] = capability_objects['container']

        # construct response
        request.setResponseCode(OK)
        request.setHeader('Content-Type', CDMI_CAPABILITY)
        request.setHeader('X-CDMI-Specification-Version', CDMI_VERSION)
        return json.dumps(body)
