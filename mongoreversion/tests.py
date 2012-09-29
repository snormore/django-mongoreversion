from django.contrib.auth.models import User
from mongoreversion.models import Revision
from mongoreversion.testcases import MongoTestCase

def create_and_save_sample_user(suffix=''):
    username = 'user%s' % (suffix, )
    email = '%s@example.com' % (username, )
    return User.objects.create(username=username, email=email)

class RevisionModelTest(MongoTestCase):
    """
        Test the Revision document model.

        TODO: Add a comprehensive suite of tests for development.
    """

    def test_create_revision(self):
        user = create_and_save_sample_user()
        obj = create_sample_revisioned_object()
        comment = 'sample comment...'
        revision = Revision.create_revision(user, obj, comment)
        self.assertTrue(revision)
        self.assertTrue(revision.pk)
        self.assertTrue(revision.timestamp)
        self.assertTrue(revision.instance_type)
        self.assertTrue(revision.instance_data)
        # TODO: more...


