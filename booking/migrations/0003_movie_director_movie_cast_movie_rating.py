import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("booking", "0002_movie_poster_image")]

    operations = [
        migrations.AddField(
            model_name="movie",
            name="director",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="movie",
            name="cast",
            field=models.TextField(blank=True, help_text="Separate cast names with commas."),
        ),
        migrations.AddField(
            model_name="movie",
            name="rating",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                help_text="Optional rating from 0 to 10.",
                max_digits=3,
                null=True,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)],
            ),
        ),
    ]
