# -*- coding: utf-8 -*-


from django.db import models, migrations


def quantity_compute(card):
    """Return the quantity of this card in all places (not deposits).

    Utility function, primarily used for a data migration. Use the
    Card.quantity field to query the db.

    return: int
    """
    quantity = 0
    if card.placecopies_set.count():
        quantity = sum([pl.nb for pl in card.placecopies_set.all()])
    return quantity

def set_card_quantity(apps, schema_director):
    """Set the new field Card.quantity with the quantity of the cards in
    places (not deposits).

    """
    Card = apps.get_model("search", "Card")
    for card in Card.objects.all():
        card.quantity = quantity_compute(card)
        card.save()

class Migration(migrations.Migration):

    dependencies = [
        ('search', '0005_auto_20151201_1700'),
    ]

    operations = [
        migrations.RunPython(set_card_quantity)
    ]
