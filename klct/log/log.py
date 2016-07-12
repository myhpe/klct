import os
import logging.config


log_dir = (os.path.dirname(os.path.abspath(__file__)))
curdir = os.getcwd()
os.chdir(log_dir)
print(__name__)

logging.config.fileConfig('logging.conf')
LOG = logging.getLogger(__name__)

os.chdir(curdir)

class FormatValidator(object):

    def __init__(self, file_path):
        self.file_path = file_path

    def file_exists(self):

        if not os.path.exists(self.file_path):
            msg = "Directory/file not exists: {}".format(self.file_path)
            LOG.error(msg)
            #LOG.error("Directory/file not exists: %s", self.file_path)
            return {'exit_status': 0, 'message': msg}

        msg = "Valid file path name: {}".format(self.file_path)
        LOG.info(msg)
        return {'exit_status': 1, 'message': msg}

    def is_conf(self):
        return True

    def isYaml(self):
        pass


# if __name__ == '__main__':
#     file_validator = FormatValidator("configTool.py")