from django.contrib.auth.models import User
from mongoreversion.models import Revision, ReversionedDocument, ContentType
from mongotesting import MongoTestCase
from mongoengine.document import Document
from mongoengine.fields import DictField, StringField, ReferenceField, IntField, DateTimeField, ListField
from django.template.defaultfilters import slugify

class MongoUser(Document):
    username = StringField(max_length=255)
    email = StringField(max_length=255)

def create_and_save_sample_user(suffix=''):
    username = 'user%s' % (suffix, )
    email = '%s@example.com' % (username, )
    return User.objects.create(username=username, email=email)

def create_and_save_sample_mongo_user(suffix=''):
    username = 'user%s' % (suffix, )
    email = '%s@example.com' % (username, )
    return MongoUser.objects.create(username=username, email=email)

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

class SampleReversionedDocument(ReversionedDocument):
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

def create_sample_reversioned_document():
    tag_models = []
    for i in range(3):
        title = 'Sample Tag %s' % (i, )
        tag = SampleTag(slug=slugify(title), title=title)
        tag_models.append(tag)
    doc = SampleReversionedDocument(slug='sample-doc-slug', title='Sample Document Title', tag_strings=['one', 'two', 'three', ], tag_models=tag_models)
    return doc

def save_revision_and_check(test, user, doc, comment=None, is_diff=True):
    revision, is_new = Revision.save_revision(user, doc, comment)
    test.assertEqual(is_new, is_diff)
    test.assertTrue(revision)
    test.assertTrue(revision.pk)
    test.assertTrue(revision.timestamp)
    test.assertTrue(revision.instance_type)
    test.assertEqual(revision.instance_type.class_name, doc._class_name)
    test.assertTrue(revision.instance_data)
    for key, value in revision.instance_data.items():
        if key in revision.related_field_types:
            field_model = revision.related_field_types.get(key)
            value = [field_model.objects.get(pk=v) for v in value]
        test.assertEqual(value, getattr(doc, key, None))
    return revision

class RevisionModelTest(MongoTestCase):

    def test_create_revision_initial(self):
        """
            Test creating a document initial revision
        """
        user = create_and_save_sample_user()
        doc = create_sample_revisioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        save_revision_and_check(self, user, doc, 'sample comment...')

    def test_create_revision_initial_with_mongouser(self):
        """
            Test creating a document initial revision with a mongo user as author
        """
        user = create_and_save_sample_mongo_user()
        doc = create_sample_revisioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        save_revision_and_check(self, user, doc, 'sample comment...')

    def test_create_reversioned_document_initial(self):
        """
            Test creating a document initial revision
        """
        user = create_and_save_sample_user()
        doc = create_sample_reversioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        save_revision_and_check(self, user, doc, 'sample comment...')

    def test_create_reversioned_document_initial_with_mongouser(self):
        """
            Test creating a document initial revision with a mongo user as author
        """
        user = create_and_save_sample_mongo_user()
        doc = create_sample_reversioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        save_revision_and_check(self, user, doc, 'sample comment...')

    def test_create_revision_with_no_diff(self):
        """
            Test creating a revision with a document that has no changes from 
            the previous revision.
        """
        user = create_and_save_sample_user()
        doc = create_sample_revisioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        save_revision_and_check(self, user, doc, 'sample comment...')
        save_revision_and_check(self, user, doc, 'sample comment...', is_diff=False)

    def test_create_revision_with_diff(self):
        """
            Test creating a revision with a document that has no changes from 
            the previous revision.
        """
        user = create_and_save_sample_user()
        doc = create_sample_revisioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        save_revision_and_check(self, user, doc, 'sample comment...')
        doc.title = 'New Sample Title'
        save_revision_and_check(self, user, doc, 'another sample comment...')

    def test_create_mongouser_revision_with_diff(self):
        """
            Test creating a revision with a document that has no changes from 
            the previous revision.
        """
        user = create_and_save_sample_mongo_user()
        doc = create_sample_revisioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        save_revision_and_check(self, user, doc, 'sample comment...')
        doc.title = 'New Sample Title'
        save_revision_and_check(self, user, doc, 'another sample comment...')

    def test_create_mongouser_revision_with_diff(self):
        """
            Test creating a revision with a document that has no changes from 
            the previous revision.
        """
        user = create_and_save_sample_mongo_user()
        doc = create_sample_revisioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        save_revision_and_check(self, user, doc, 'sample comment...')
        doc.title = 'New Sample Title'
        save_revision_and_check(self, user, doc, 'another sample comment...')

    def test_revert_revision(self):
        """
            Test reverting a document back to a specific revision.
        """
        user = create_and_save_sample_user()
        doc = create_sample_revisioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        rev1 = save_revision_and_check(self, user, doc, 'sample comment...')
        doc1_id = doc.pk
        doc.title = 'New Sample Title'
        rev2 = save_revision_and_check(self, user, doc, 'another sample comment...')
        doc1 = rev1.revert()
        doc1 = SampleDocument.objects.get(pk=doc1_id)
        self.assertNotEqual(doc1.title, rev2.instance.title)
        self.assertEqual(doc1.title, rev1.instance.title)

    def test_revert_mongouser_revision(self):
        """
            Test reverting a document back to a specific revision.
        """
        user = create_and_save_sample_mongo_user()
        doc = create_sample_revisioned_document()
        for tag in doc.tag_models:
            save_revision_and_check(self, user, tag)
        rev1 = save_revision_and_check(self, user, doc, 'sample comment...')
        doc1_id = doc.pk
        doc.title = 'New Sample Title'
        rev2 = save_revision_and_check(self, user, doc, 'another sample comment...')
        doc1 = rev1.revert()
        doc1 = SampleDocument.objects.get(pk=doc1_id)
        self.assertNotEqual(doc1.title, rev2.instance.title)
        self.assertEqual(doc1.title, rev1.instance.title)

class ReversionedDocumentTest(MongoTestCase):

    def test_is_versioned(self):
        doc = create_sample_reversioned_document()
        doc._meta['versioned'] = True
        self.assertEqual(True, doc.is_versioned)
        doc._meta['versioned'] = False
        self.assertEqual(False, doc.is_versioned)
        doc._meta['versioned'] = True

    def test_revisions(self):
        user = create_and_save_sample_user()
        doc = create_sample_reversioned_document()
        for tag in doc.tag_models:
            tag.save()
        doc.save()
        ContentType.objects.create(class_name=doc._class_name)

        self.assertEqual(0, doc.revisions.count())
        doc.slug = 'new-sample-slug'
        save_revision_and_check(self, user, doc, 'sample comment...')
        self.assertEqual(1, doc.revisions.count())



