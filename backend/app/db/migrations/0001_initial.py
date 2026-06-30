from tortoise import migrations
from tortoise.migrations import operations as ops
from app.db.schema import MediaKind, ReferenceType
from uuid import uuid4
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Reference',
            fields=[
                ('id', fields.UUIDField(primary_key=True, default=uuid4, unique=True, db_index=True)),
                ('type', fields.CharEnumField(description='REFERENCE: reference\nCOMPOSITION: composition\nTYPEFACE: typeface\nPALETTE: palette', enum_type=ReferenceType, max_length=20)),
                ('media', fields.CharEnumField(description='IMAGE: image\nVIDEO: video\nPDF: pdf\nWEBPAGE: webpage\nUNKNOWN: unknown', enum_type=MediaKind, max_length=20)),
                ('original_name', fields.CharField(max_length=255)),
                ('stored_name', fields.CharField(max_length=255)),
                ('bucket', fields.CharField(max_length=255)),
                ('object_path', fields.CharField(max_length=1024)),
                ('is_processed', fields.BooleanField(default=False)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'references', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
    ]
