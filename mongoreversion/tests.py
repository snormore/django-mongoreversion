from django.contrib.auth.models import User
from mongoreversion.models import Revision
from mongoreversion.testcases import MongoTestCase
from mongoengine.document import Document
from mongoengine.fields import DictField, StringField, ReferenceField, IntField, DateTimeField, ListField
from django.template.defaultfilters import slugify

def create_and_save_sample_user(suffix=''):
    username = 'user%s' % (suffix, )
    email = '%s@example.com' % (username, )
    return User.objects.create(username=username, email=email)

class SampleTag(Document):
    slug = StringField(max_length=100)
    title = StringField(max_length=100)

    meta = {
        'versioned': True, 
        'versioned_fields': ['title', 'slug', ], 
        'versioned_related': [], 
    }

class SampleDocument(Document):
    slug = StringField(max_length=100)
    title = StringField(max_length=100)
    tag_strings = ListField(StringField())
    tag_models = ListField(ReferenceField(SampleTag, dbref=False))

    meta = {
        'versioned': True, 
        'versioned_fields': ['title', 'slug', ], 
        'versioned_related': ['tag_models', ], 
    }

def create_sample_revisioned_document():
    tag_models = []
    for i in range(3):
        title = 'Sample Tag %s' % (i, )
        tag = SampleTag(slug=slugify(title), title=title)
        tag_models.append(tag)
    doc = SampleDocument(slug='sample-doc-slug', title='Sample Document Title', tag_strings=['one', 'two', 'three', ], tag_models=tag_models)
    return doc

class RevisionModelTest(MongoTestCase):
    """
        Test the Revision document model.

        TODO: Add a comprehensive suite of tests for development.
    """

    def test_create_revision(self):
        user = create_and_save_sample_user()
        doc = create_sample_revisioned_document()
        for tag in doc.tag_models:
            Revision.create_revision(user, tag)
        comment = 'sample comment...'
        revision = Revision.create_revision(user, doc, comment)
        self.assertTrue(revision)
        self.assertTrue(revision.pk)
        self.assertTrue(revision.timestamp)
        self.assertTrue(revision.instance_type)
        self.assertEqual(revision.instance_type.class_name, doc._class_name)
        self.assertTrue(revision.instance_data)
        for key, value in revision.instance_data.items():
            if key in revision.related_field_types:
                field_model = revision.related_field_types.get(key)
                value = [field_model.objects.get(pk=v) for v in value]
            self.assertEqual(value, getattr(doc, key, None))

    def test_revert_revision(self):
        pass
        # TODO: implement this...



