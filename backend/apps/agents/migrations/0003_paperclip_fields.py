# Generated manually — Paperclip-Integrationsfelder

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0002_add_agent_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentcompanyconfig',
            name='use_paperclip',
            field=models.BooleanField(
                default=True,
                help_text='Paperclip als Vermittler nutzen (statt Agent-Agency direkt)',
            ),
        ),
        migrations.AddField(
            model_name='agentcompanyconfig',
            name='paperclip_base_url',
            field=models.CharField(
                default='http://paperclip-app:3100',
                help_text='Paperclip API-Basis-URL',
                max_length=500,
            ),
        ),
        migrations.AddField(
            model_name='agentcompanyconfig',
            name='paperclip_company_id',
            field=models.CharField(
                blank=True,
                help_text='Paperclip Company-UUID',
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name='agentcompanyconfig',
            name='paperclip_api_key',
            field=models.CharField(
                blank=True,
                help_text='Paperclip Board-API-Key',
                max_length=255,
            ),
        ),
    ]
