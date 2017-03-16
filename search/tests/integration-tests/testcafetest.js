// Copyright 2014 - 2017 The Abelujo Developers
// See the COPYRIGHT file at the top-level directory of this distribution

// Abelujo is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// Abelujo is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

// Use testcafe for integration tests.
// Like Selenium, but easier install, no plugins.
// https://devexpress.github.io/testcafe/documentation/getting-started/

// Unfortunately, we can't use Livescript yet:
// https://github.com/gkz/LiveScript/pull/836

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
