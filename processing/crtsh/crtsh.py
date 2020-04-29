import os
import sys
import json

from fame.core.module import ProcessingModule
from fame.common.utils import tempdir
from fame.common.exceptions import ModuleInitializationError, ModuleExecutionError

try:
    import requests
    has_requests = True
except ImportError:
    has_requests = False

try:
    import tldextract
    has_tldextract = True
except ImportError:
    has_tldextract = False

class Crtsh(ProcessingModule):
    name = "crtsh"
    description = "Gather all domain certificates using Crt.sh"
    acts_on = ['url']

    config = [
        {
            'name': 'save_json',
            'type': 'bool',
            'default': True,
            'description': 'Save certificate information as json output.'
        },
        {
            'name': 'save_hosts',
            'type': 'bool',
            'default': True,
            'description': 'Save found hostnames in a file list.'
        },
        {
            'name': 'cert_count',
            'type': 'integer',
            'default': 10,
            'description': 'Number of most recent certs to show in report.'
        },
    ]

    def initialize(self):
        if not has_requests:
            raise ModuleInitializationError(self, "Missing dependancy: requests")
        if not has_tldextract:
            raise ModuleInitializationError(self, "Missing dependancy: tldextract")

    def each(self, target):
        tmpdir = tempdir()
        self.results = {}
        self.results['cert_count'] = self.cert_count

        # Get the root domain
        url = target
        domain = tldextract.extract(url)
        root_domain = "{}.{}".format(domain.domain, domain.suffix)

        self.log("info", "Querying crt.sh with root domain...")
        try:
            req = requests.get("https://crt.sh/?q=%.{}&output=json".format(root_domain))
            json_data = json.loads(req.text)
        except:
            raise ModuleExecutionError("Failed to get data from crt.sh")
        
        # We want to gather data in a way to present the details.html template as default
        vc = 0
        certs = []
        for (key, value) in enumerate(json_data):
            if vc < self.cert_count:
                entry = {'id': value['id'], 'issuer_name': value['issuer_name'], 'name_value': value['name_value'], 'entry_timestamp': value['entry_timestamp']}
                certs.append(entry)
                vc += 1
        self.results['top_certs'] = certs

        # Save JSON data
        if self.save_json:
            self.log("info", "Saving json output from crt.sh...")
            json_file = "{}.json".format(domain.domain)
            json_save = os.path.join(tmpdir, json_file)
            try:
                with open(json_save, "w") as jf:
                    jf.write(json.dumps(json_data, indent=4))
                    jf.close()
                self.add_support_file('Json Output', json_save)
            except:
                raise ModuleExecutionError("Failed to save json data from crt.sh")

        # Save host list
        if self.save_hosts:
            self.log("info", "Saving host list...")
            host_file = "{}_hostlist.txt".format(domain.domain)
            host_save = os.path.join(tmpdir, host_file)
            values = []
            for item in json_data:
                entry = item['name_value'].split('\n')
                for e in entry:
                    values.append(e)
            dedupe = set(values)
            preview = ""
            try:
                with open(host_save, "w") as hf:
                    for item in list(dedupe):
                        host = "{}\r\n".format(item)
                        hf.write(host)
                        preview += host
                    hf.close()
                self.add_support_file('Host List', host_save)
                self.results['host_list'] = preview
            except:
                raise ModuleExecutionError("Failed to save json data from crt.sh")

        self.log("info","crt.sh finished.")

        return True