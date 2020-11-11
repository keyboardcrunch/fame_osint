import os
import subprocess

from fame.core.module import ProcessingModule
from fame.common.utils import tempdir
from fame.common.exceptions import ModuleInitializationError, ModuleExecutionError

class StringAnalysis(ProcessingModule):
    name = "string_analysis"
    description = "Strings file analysis."
    acts_on = ["executable","pdf"]

    def initialize(self):
        pass

    def each(self, target):
        self.results = {}

        results_text = subprocess.check_output(['strings', '-a', '-w', target])
        self.results['strings'] = results_text
        
        return True
