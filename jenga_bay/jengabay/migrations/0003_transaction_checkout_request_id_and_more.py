# Generated by Django 5.0.7 on 2024-09-15 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jengabay', '0002_auto_20211124_1334'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='checkout_request_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='merchant_request_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='payment_status',
            field=models.CharField(default='Pending', max_length=50),
        ),
        migrations.AddField(
            model_name='transaction',
            name='phone_number',
            field=models.CharField(default='0745987667', max_length=15),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_code',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
