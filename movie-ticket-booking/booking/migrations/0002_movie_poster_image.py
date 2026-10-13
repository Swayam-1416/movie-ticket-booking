from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("booking", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="movie",
            name="poster_image",
            field=models.ImageField(blank=True, upload_to="movie_posters/"),
        ),
    ]
