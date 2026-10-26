from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('finsavvy', '0005_aviso'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='custocompra',
            options={'ordering': ['-data', '-id']},
        ),
        migrations.RenameField(
            model_name='custocompra',
            old_name='nome',
            new_name='estabelecimento',
        ),
        migrations.RenameField(
            model_name='custocompra',
            old_name='valor',
            new_name='valor_total',
        ),
        migrations.AlterField(
            model_name='custocompra',
            name='valor_total',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='custocompra',
            name='data',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.RemoveField(
            model_name='custocompra',
            name='qr_data',
        ),
        migrations.AddField(
            model_name='custocompra',
            name='qr_code_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.CreateModel(
            name='ItemCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=255)),
                ('quantidade', models.FloatField(default=1.0)),
                ('valor_unitario', models.FloatField(default=0.0)),
                ('valor_total_item', models.FloatField(default=0.0)),
                ('compra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='finsavvy.custocompra')),
            ],
        ),
    ]
