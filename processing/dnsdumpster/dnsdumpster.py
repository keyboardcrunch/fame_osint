import os
import sys

from fame.core.module import ProcessingModule
from fame.common.constants import VENDOR_ROOT
from fame.common.utils import tempdir
from fame.common.exceptions import ModuleInitializationError

try:
    sys.path.append(os.path.join(VENDOR_ROOT, 'dnsdmpstr'))
    import dnsdmpstr
    has_dnsdump = True
except ImportError:
    has_dnsdump = False

try:
    import tldextract
    has_tldextract = True
except ImportError:
    has_tldextract = False

class DnsDumpster(ProcessingModule):
    name = "dnsdumpster"
    description = "Enumerate domain DNS data."
    acts_on = ['url']

    config = [
        {
            'name': 'reverse_dns',
            'type': 'bool',
            'default': False,
            'description': 'List reverse DNS entries from DnsDumpster.'
        },
        {
            'name': 'page_links',
            'type': 'bool',
            'default': False,
            'description': 'Grab page links using HackerTarget.'
        },
        {
            'name': 'http_headers',
            'type': 'bool',
            'default': False,
            'description': 'Grab HTTP server headers from URL using HackerTarget.'
        },
        {
            'name': 'save_json',
            'type': 'bool',
            'default': False,
            'description': 'Save DNS lookup data to a json file.'
        },
    ]

    def initialize(self):
        if not has_dnsdump:
            raise ModuleInitializationError(self, "Missing dependancy: dnsdmpstr")
        if not has_tldextract:
            raise ModuleInitializationError(self, "Missing dependancy: tldextract")

    def each(self, target):
        self.results = {}
        dns_info = ""

        # Get the root domain
        url = target
        domain = tldextract.extract(url)
        root_domain = "{}.{}".format(domain.domain, domain.suffix)
        self.log("info", 'gathering dns data for {}'.format(root_domain))

        # Initialize dnsdmpstr and enumerate the data
        dnsdump = dnsdmpstr.dnsdmpstr()

        # DNS Data
        data = dnsdump.dump(root_domain)
        for (key,value) in enumerate(data):
            # we'll handle any NS, MX, TXT records and drop the rest (shouldn't be others)
            dns_info += "\n\n{}\n".format(value)
            if value == 'dns':
                for entry in data[value]:
                    dns_info += "{}\n".format(data[value][entry]["host"])
            if value == 'mx':
                for entry in data[value]:
                    dns_info += "{} : {}\n".format(data[value][entry]["host"], data[value][entry]["ip"])
            if value == 'host':
                for entry in data[value]:
                    # Example: {'ip': '35.239.11.185', 'host': 'webdisk.pynative.comFTP: 220-##############################################HTTP TECH: nginxHTTPS TECH: nginx'}
                    host = data[value][entry]["host"].replace("FTP", "\tFTP").replace("HTTP", "\tHTTP") # formatting cleanup
                    dns_info += "{} \t {}\n".format(host, data[value][entry]["ip"])
            if value == 'txt':
                for entry in data[value]:
                    dns_info += "{}\n".format(data[value][entry])
            else:
                pass
        self.results['dns_data'] = dns_info

        # Save csv data
        if self.save_json:
            import json
            try:
                tmpdir = tempdir()
                json = json.dumps(dnsdump.dnslookup(root_domain), indent=4, separators=(',',':'))
                json_file = "{}.json".format(domain.domain)
                json_save = os.path.join(tmpdir, json_file)
                with open(json_save, "w") as cf:
                    cf.write(json)
                    cf.close()
                self.add_support_file("DNS Data", json_save)
            except:
                self.log("error", 'failed to save json output.')
                pass

        # Reverse DNS
        if self.reverse_dns:
            self.log("info", 'gathering reverse dns data...')
            self.results['reverse_dns'] = dnsdump.reversedns(root_domain)

        # HTTP Headers
        if self.http_headers:
            self.log("info", 'gathering url headers...')
            # Query HackerTarget with a cleaned up target URL
            dest = url.split('?')[0].split("#")[0]  # reduce dnsdmpstr errors
            headers = dnsdump.httpheaders(dest)
            if not "error" in headers:
                self.results['headers'] = headers

        # Page Links
        if self.page_links:
            self.log("info", 'gathering url links...')
            # Query HackerTarget with a cleaned up target URL
            dest = url.split('?')[0].split("#")[0]  # reduce dnsdmpstr errors
            links = dnsdump.pagelinks(dest)
            if not "url is invalid" in links:
                self.results['links'] = links

        return True