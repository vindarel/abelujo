# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

"""
Delete test places that are created by the buggy test runner...
"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from search.models import Place

# py2/3
try:
    input = raw_input
except NameError:
    pass


class Command(BaseCommand):

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        Place.delete_test_places()
        self.stdout.write("OK")
