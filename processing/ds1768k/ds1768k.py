import os
from fame.common.utils import tempdir
from fame.core.module import ProcessingModule
from fame.common.exceptions import ModuleInitializationError
from ..docker_utils import HAVE_DOCKER, docker_client, temp_volume


class DS1768k(ProcessingModule):
    name = "ds1768k"
    description = "Dump and decode Cobalt Strike beacons."
    acts_on = ["exe", "dll"]

    def initialize(self):
        if not HAVE_DOCKER:
            raise ModuleInitializationError(self, "Missing dependency: docker")

        return True

    def run_1768k(self, target):
        args = "/data/{} --output /data/output/results.txt".format(target)

        return docker_client.containers.run(
            'fame/ds1768k',
            args,
            volumes={self.outdir: {'bind': '/data', 'mode': 'rw'}},
            stderr=True,
            remove=True
        )

    def each(self, target):
        self.results = {
            'beacon': u''
        }

        self.outdir = temp_volume(target)
        results_dir = os.path.join(self.outdir, "output")

        self.run_1768k(os.path.basename(target))

        with open(os.path.join(results_dir, 'results.txt')) as beacon_data:
            line_count = sum(1 for _ in beacon_data)
            if line_count > 1:
                self.results['beacon'] = self.results['beacon'] + "\r\n" + beacon_data

        if len(self.results['beacon']) > 0:
            return True
