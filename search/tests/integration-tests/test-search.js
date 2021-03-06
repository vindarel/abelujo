// Copyright 2014 - 2020 The Abelujo Developers
// See the COPYRIGHT file at the top-level directory of this distribution

// Abelujo is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Abelujo is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.

// You should have received a copy of the GNU Affero General Public License
// along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

import { Selector } from 'testcafe';

async function login (t) {
    await t
        .typeText('#id_username', 'admin')
        .typeText('#id_password', 'admin')
        .click('#submit_button');
};

fixture `search`
    .page `http://localhost:8000/fr/search`

test('search and see results', async t => {
    await login(t);
    await t
        .typeText('#default-input', 'antigone')
        .click('#submit-button');
    const cardsCount = await Selector('#card').count;
    await t.expect(cardsCount).exists;

});
