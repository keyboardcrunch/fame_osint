from __future__ import unicode_literals
import json
from fame.common.exceptions import ModuleInitializationError
from fame.core.module import ReportingModule

try:
    import pymsteams
    HAS_TEAMS = True
except ImportError:
    HAS_TEAMS = False

try:
    from defang import defang
    HAS_DEFANG = True
except ImportError:
    HAS_DEFANG = False


class Teams(ReportingModule):
    name = "msteams"
    description = "Post message on MS Teams when an anlysis if finished."

    config = [
        {
            'name': 'url',
            'type': 'str',
            'description': 'Incoming webhook URL.'
        },
        {
            'name': 'fame_base_url',
            'type': 'str',
            'description': 'Base URL of your FAME instance, as you want it to appear in links.'
        },
    ]

    def initialize(self):
        if ReportingModule.initialize(self):
            if not HAS_TEAMS:
                raise ModuleInitializationError(self, "Missing dependency: pymsteams")

            if not HAS_DEFANG:
                raise ModuleInitializationError(self, "Missing dependency: defang")

            return True
        else:
            return False

    def done(self, analysis):
        # Teams connector
        message = pymsteams.connectorcard(self.url)

        # Compile and send message
        message.title("FAME Analysis Completed")
        message.summary("New analysis ready for review at: {0}/analyses/{1}".format(self.fame_base_url, analysis['_id']))

        target_section = pymsteams.cardsection()
        target_section.title("Targets")
        target_section.text(defang(', '.join(analysis._file['names'])))
        message.addSection(target_section)

        # May want to use addFact() on below sections for showing lists
        if analysis['modules'] is not None:
            module_section = pymsteams.cardsection()
            module_section.title("Analysis Modules")
            module_section.text(', '.join(analysis['modules']))
            message.addSection(module_section)

        if len(analysis['extractions']) > 0:
            extraction_section = pymsteams.cardsection()
            extraction_section.title("Extracted Items")
            extraction_section.text("{0}".format(','.join([x['label'] for x in analysis['extractions']])))
            message.addSection(extraction_section)

        if len(analysis['probable_names']) > 0:
            classification_section = pymsteams.cardsection()
            classification_section.title("Probably Names")
            classification_section.text("{0}".format(','.join(analysis['probable_names'])))
            message.addSection(classification_section)

        message.addLinkButton("View Analysis", "{0}/analyses/{1}".format(self.fame_base_url, analysis['_id']))
        message.send()
