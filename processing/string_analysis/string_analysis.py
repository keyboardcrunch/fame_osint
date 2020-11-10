import os


from fame.core.module import ProcessingModule
from fame.common.utils import tempdir
from fame.common.exceptions import ModuleInitializationError

from ..docker_utils import HAVE_DOCKER, docker_client, temp_volume

class StringAnalysis(ProcessingModule):
    name = "string_analysis"
    description = "Strings file analysis."
    acts_on = ["executable","pdf","txt","rtf","vbscript","javascript","html","dll"]

    def initialize(self):
        if not HAVE_DOCKER:
            raise ModuleInitializationError(self, "Missing dependency: docker")
        return True

    def run_strings(self, target):
        args = "-a /data/{} >> /data/output/results.txt".format(target)

        return docker_client.containers.run(
            'fame/string_analysis',
            args,
            volumes={self.outdir: {'bind': '/data', 'mode': 'rw'}},
            stderr=True,
            remove=True
        )

    def each(self, target):
        self.results = {}

        self.outdir = temp_volume(target)
        results_dir = os.path.join(self.outdir, "output")

        self.run_strings(os.path.basename(target))

        with open(os.path.join(results_dir, "results.txt"), "r") as results_text:
            self.results['strings'] = results_text.readlines()

        if len(self.results['strings']) > 0:
            return self.results['strings']
