# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

"""
For all cards with a librairie-de-paris cover image, get a higher res one.
"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from search.models import Card

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        cards = Card.objects.filter(cover__startswith="https://images.epagine.fr")
        self.stdout.write("Updating {} cards...".format(cards.count()))
        for card in cards:
            val = card.cover.replace('_m.jpg', '_75.jpg')
            card.cover = val
            card.save()
        self.stdout.write("OK")
