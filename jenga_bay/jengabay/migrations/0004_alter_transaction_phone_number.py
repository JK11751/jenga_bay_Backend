# Generated by Django 5.0.7 on 2024-11-02 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jengabay', '0003_transaction_checkout_request_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='phone_number',
            field=models.CharField(default='254745987667', max_length=15),
        ),
    ]