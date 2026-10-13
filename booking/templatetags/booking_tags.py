from django import template

register = template.Library()


@register.filter
def split_genres(value):
    if not value:
        return []
    return [genre.strip() for genre in value.replace("·", ",").split(",") if genre.strip()]
