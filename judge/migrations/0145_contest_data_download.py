from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0144_submission_index_cleanup'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='data_last_downloaded',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last data download time'),
        ),
    ]