import os
import subprocess

from fame.core.module import ProcessingModule
from fame.common.utils import tempdir
from fame.common.exceptions import ModuleInitializationError, ModuleExecutionError

class StringAnalysis(ProcessingModule):
    name = "string_analysis"
    description = "Strings file analysis."
    acts_on = ["executable","pdf","excel", "xls", "xlsm"]
    
    triggered_by = "!"  # manual use only 

    def initialize(self):
        pass

    def each(self, target):
        self.results = {}
        command = "strings -a -w %s" % target
        results_text = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        self.results['strings'] = results_text
        
        return True
