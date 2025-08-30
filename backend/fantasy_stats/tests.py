import logging
from django.test import TestCase

# Create your tests here.
import django

logger = logging.getLogger(__name__)
logger.info(django.get_version())
