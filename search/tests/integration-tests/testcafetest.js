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

// Use testcafe for integration tests.
// Like Selenium, but easier install, no plugins.
// https://devexpress.github.io/testcafe/documentation/getting-started/

// Unfortunately, we can't use Livescript yet:
// https://github.com/gkz/LiveScript/pull/836

import { Selector } from 'testcafe';

fixture `abelujo`
    .page `http://localhost:8000/en/`;

test('See the login page', async t => {
    const location = await t.eval( () => window.location);
    await t.expect(location.pathname).eql('/login/');
});

async function login (t) {
    await t
        .typeText('#id_username', 'admin')
        .typeText('#id_password', 'admin')
        .click('#submit_button');
};

test('log in', async t => {
    await login(t);
    const location = await t.eval( () => window.location);
    await t.expect(location.pathname).eql('/en/');
});

fixture `deposits view`
    .page `http://localhost:8000/en/deposits`;

test('see the deposits list', async t => {
    await login(t);
    const location = await t.eval( () => window.location);
    await t.expect(location.pathname).eql('/en/deposits/');
    // and test something useful !
});

fixture `deposits view`
    .page `http://localhost:8000/en/inventories/1`;

test('see an inventory', async t => {
    await login(t);
    const location = await t.eval( () => window.location);
    // Yes, the test is dependent of the DB state :S
    await t.expect(location.pathname).eql('/en/inventories/1');
    const title = await Selector('#title').textContent;
    // Here "default place" shows that some variables are loaded,
    // i.e. some api calls worked.
    await t.expect(title).eql('Inventory of default place');
});

fixture `To Command`
    .page `http://localhost:8000/en/commands/`;

test('see the To Command list', async t => {
    await login(t);
    const location = await t.eval( () => window.location);
    await t.expect(location.pathname).eql('/en/commands/');
    const title = await Selector('#distributors').count;
    await t.expect(title).eql(1);
});
