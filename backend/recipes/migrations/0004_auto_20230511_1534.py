# Generated by Django 3.2.18 on 2023-05-11 15:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20230511_1419'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipe',
            options={'ordering': ('-id',), 'verbose_name': 'Рецепт'},
        ),
        migrations.RenameField(
            model_name='ingredientquantity',
            old_name='quantity',
            new_name='amount',
        ),
        migrations.AlterField(
            model_name='ingredientquantity',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amount', to='recipes.ingredient', verbose_name='Ингридиент'),
        ),
        migrations.AlterField(
            model_name='ingredientquantity',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amount', to='recipes.recipe', verbose_name='Рецепт'),
        ),
    ]