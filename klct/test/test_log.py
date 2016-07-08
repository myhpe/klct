import logging
from klct.log import logger

LOG = logging.getLogger(__name__)


def test_log_sample():
    LOG.info("test log in klct.ldap test_log_sample")


class TestLogClassSample(object):
    def __init__(self):
        LOG.info("test log in klct.ldap TestLogClassSample init")

    def log_sample(self):
        LOG.info("test log in klct.ldap TestLogClassSample log_sample")


if __name__ == '__main__':
    LOG.info("test log in klct.ldap main")
    test_log_sample()

    sample = TestLogClassSample()
    sample.log_sample()

