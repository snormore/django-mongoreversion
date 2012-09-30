from django.db import models
from mongoengine.document import Document
from mongoengine.fields import DictField, StringField, ReferenceField, IntField, DateTimeField, ListField, ObjectIdField
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from datetime import datetime
from mongoengine.base import _document_registry

class ContentType(Document):
    class_name = StringField(max_length=100, unique=True)

    def __unicode__(self):
        return self.class_name

    def document_model(self):
        return _document_registry.get(self.class_name, None)

class Revision(Document):
    user_id = IntField(required=True)
    timestamp = DateTimeField(default=datetime.now, required=True)
    instance_data = DictField()
    instance_related_revisions = DictField()
    instance_type = ReferenceField(ContentType, dbref=False, required=True)
    instance_id = ObjectIdField(required=True)
    comment = StringField(required=False)

    def __init__(self, *args, **kwargs):
        super(Revision, self).__init__(*args, **kwargs)
        
        # create lookup of related field types
        related_field_types = {}
        instance_model = self.instance_type.document_model()
        for key, field in instance_model._fields.items():
            related_field_type = None
            if isinstance(field, ListField):
                if isinstance(field.field, ReferenceField):
                    related_field_type = field.field.document_type_obj
            elif isinstance(field, ReferenceField):
                related_field_type = field.document_type_obj
            if related_field_type:
                related_field_types[key] = related_field_type
        self.related_field_types = related_field_types


    def __unicode__(self):
        return '<Revision user=%s, time=%s, type=%s, comment=%s, >' % (self.user_id, self.timestamp, self.instance_type, self.comment, )

    @property
    def instance(self):
        instance_model = self.instance_type.document_model()
        data = dict(self.instance_data)
        for key, value in data.items():
            if key in self.related_field_types:
                if key in self.instance_related_revisions:
                    revision_value = self.instance_related_revisions.get(key)
                    if isinstance(revision_value, (list, tuple)):
                        values = []
                        for i, rev_id in enumerate(revision_value):
                            if rev_id:
                                revision = Revision.objects.get(pk=rev_id)
                                values.append(revision.instance)
                            else:
                                obj_id = value[i]
                                values.append(self.related_field_types.get(key).objects.get(pk=obj_id))
                        data[key] = values
                    else:
                        if value:
                            revision = Revision.objects.get(pk=value)
                            data[key] = revision.instance
                        else:
                            data[key] = self.related_field_types.get(key).objects.get(pk=value)
                else:
                    if isinstance(value, (list, tuple)):
                        data[key] = [self.related_field_types.get(key).objects.get(pk=v) for v in value]
                    else:
                        data[key] = self.related_field_types.get(key).objects.get(pk=value)
        return instance_model(**data)

    @property
    def user(self):
        try:
            return User.objects.get(pk=self.user_id)
        except User.DoesNotExist:
            return None

    def diff(self, revision=None):
        """
            Returns the diff of the current revision with the given revision.
            If the given revision is empty, use the latest revision of the 
            document instance.
        """
        if not revision:
            revision = Revision.latest_revision(self.instance)
        if not revision:
            return self.instance_data
        diff_dict = {}
        for key, value in self.instance_data.items():
            if value != revision.instance_data.get(key):
                diff_dict[key] = value
        return diff_dict

    def revert(self):
        """
            Revert the associated document instance back to this revision.
            Return the document instance.
        """
        self.instance.save()
        return self.instance

    @staticmethod
    def latest_revision(instance):
        try:
            instance_type = ContentType.objects.get(class_name=instance._class_name)
            revisions = Revision.objects.filter(instance_type=instance_type, instance_id=instance.pk).order_by('-timestamp')
            if revisions.count() > 0:
                return revisions[0]
        except ContentType.DoesNotExist:
            pass
        return None

    @staticmethod
    def save_revision(user, instance, comment=None):
        if not instance._meta.get('versioned', None):
            raise ValueError('instance meta does not specify it to be versioned, set versioned=True to enable')

        instance_type, is_new = ContentType.objects.get_or_create(class_name=instance._class_name)
        instance_data = dict(instance._data)
        instance_related_revisions = {}

        # ensure instance has been saved at least once
        if not instance.pk:
            instance.save()

        # Save instance ID in data dict
        instance_data['id'] = instance.pk

        # Remove None entry if it exists
        if None in instance_data:
            del instance_data[None]

        # create lookup of related field types
        related_field_types = {}
        for key, field in instance._fields.items():
            related_field_type = None
            if isinstance(field, ListField):
                if isinstance(field.field, ReferenceField):
                    related_field_type = field.field.document_type_obj
            elif isinstance(field, ReferenceField):
                related_field_type = field.document_type_obj
            # TODO: elif isinstance(field, DictField):

            if related_field_type:
                related_field_types[key] = related_field_type

        # process field data
        for key, value in instance_data.items():

            if key in related_field_types:

                # check if related field is versioned, store revision data
                if related_field_types.get(key)._meta.get('versioned', None):

                    # versioned, store revision ID(s)
                    if isinstance(value, (list, tuple)):
                        id_revisions = []
                        for v in value:
                            revision = Revision.latest_revision(v)
                            # TODO: if latest revision doesn't exist then maybe
                            # it should be created here
                            if revision:
                                id_revisions.append(revision.pk)
                            else:
                                # if no revision exists, then explicitely 
                                # store a None entry
                                id_revisions.append(None)
                            instance_related_revisions[key] = id_revisions
                    else:
                        revision = Revision.latest_revision(value)
                        # TODO: if latest revision doesn't exist then maybe it 
                        # should be created here
                        if revision:
                            instance_related_revisions[key] = revision.pk
                        else:
                            # if no revision exists, then explicitely store a
                            # None entry
                            instance_related_revisions[key] = None

                # store object ID(s) in instance_data
                if isinstance(value, (list, tuple)):
                    instance_data[key] = [v.pk for v in value]
                else:
                    instance_data[key] = value.pk

            else:
                # store data as is
                instance_data[key] = value

        # create the revision, but do not save it yet
        revision = Revision(user_id=user.pk, timestamp=datetime.now(), instance_type=instance_type, instance_data=instance_data, instance_related_revisions=instance_related_revisions, instance_id=instance.pk, comment=comment)

        # check for any differences in data from lastest revision
        # return the latest revision if no difference
        latest_revision = Revision.latest_revision(instance)
        if latest_revision:
            diff = revision.diff(latest_revision)
            if not diff:
                return latest_revision, False

        # save revision and return
        revision.save()
        return revision, True


