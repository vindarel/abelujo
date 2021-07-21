# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

"""
Move all the cards of this place to another.

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from search.models import Preferences, Place

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--origin',
                            dest="origin",
                            action="store",
                            required=True,
                            help="origin place id.")

        parser.add_argument('--to',
                            dest="to",
                            action="store",
                            required=False,
                            help="destination place id (defaults to default place).")

    def handle(self, *args, **options):

        to = options.get('to')
        origin = options.get('origin')
        try:
            origin = Place.objects.get(id=origin)
        except ObjectDoesNotExist:
            self.stdout.write("This origin place of id {} does not exist. Nothing to do.".format(origin))
            exit(1)

        if to is None:
            to = Preferences.get_default_place()
        else:
            try:
                to = Place.objects.get(id=to)
            except ObjectDoesNotExist:
                self.stdout.write("This destination place of id {} does not exist. Nothing to do.".format(origin))
                exit(1)

        self.stdout.write("Move all the cards from {} to {} ?".format(origin, to))
        self.stdout.write("Nb of cards to move: {}".format(len(origin.cards())))  # costly cards()

        confirmation = raw_input("Continue ? [Y/n]")
        if confirmation == 'n':
            exit(0)

        default_place = Preferences.get_default_place()

        origin.move_all(default_place, with_progress=True, create_movement=False)

        # Delete the now empty place object.
        if origin.placecopies_set.count() == 0:
            origin.delete()

        self.stdout.write("-------------------")
        self.stdout.write("All done.")
