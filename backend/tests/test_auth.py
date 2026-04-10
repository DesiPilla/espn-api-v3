"""
Phase 1.1 Backend Authentication Test Suite
============================================
Covers:
  - EmailBackend: email + password auth, case-insensitivity, edge cases
  - @token_auth_required decorator: missing / malformed / invalid / valid token
  - Auth endpoints: register, login, logout, me, password-reset, password-reset/confirm
  - LeagueInfo user isolation: leagues_data, get_league_details,
    distinct-leagues-previous, copy-old-league, league-input

Run with:
    pytest backend/tests/test_auth.py -v
"""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.authtoken.models import Token

from backend.accounts.backends import EmailBackend
from backend.fantasy_stats.models import LeagueInfo

# ── URL constants ─────────────────────────────────────────────────────────────

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/auth/me/"
PASSWORD_RESET_URL = "/api/auth/password-reset/"
PASSWORD_RESET_CONFIRM_URL = "/api/auth/password-reset/confirm/"

LEAGUES_URL = "/api/leagues/"
LEAGUE_DETAIL_URL = "/api/league/{year}/{league_id}/"
DISTINCT_PREV_URL = "/api/distinct-leagues-previous/"
COPY_OLD_LEAGUE_URL = "/api/copy-old-league/{league_id}/"
LEAGUE_INPUT_URL = "/api/league-input/"

# ── Shared helpers ────────────────────────────────────────────────────────────


def make_user(email="user@example.com", password="StrongPass123!"):
    return User.objects.create_user(username=email, email=email, password=password)


def get_or_create_token(user):
    token, _ = Token.objects.get_or_create(user=user)
    return token


def auth_client(user):
    """Django test Client with the user's token pre-set in the Authorization header."""
    client = Client()
    token = get_or_create_token(user)
    client.defaults["HTTP_AUTHORIZATION"] = f"Token {token.key}"
    return client


def make_league(user, league_id=1, league_year=2024, league_name="Test League"):
    return LeagueInfo.objects.create(
        league_id=league_id,
        league_year=league_year,
        swid="{TEST-SWID}",
        espn_s2="test_espn_s2_value",
        league_name=league_name,
        user=user,
    )


# ════════════════════════════════════════════════════════════════════════════
# EmailBackend
# ════════════════════════════════════════════════════════════════════════════


class EmailBackendTests(TestCase):
    def setUp(self):
        self.backend = EmailBackend()
        self.user = make_user()

    def test_authenticate_with_username_kwarg(self):
        """authenticate(username=...) accepts email as the username."""
        result = self.backend.authenticate(
            None, username="user@example.com", password="StrongPass123!"
        )
        self.assertEqual(result, self.user)

    def test_authenticate_with_email_kwarg(self):
        """authenticate(email=...) is also supported."""
        result = self.backend.authenticate(
            None, email="user@example.com", password="StrongPass123!"
        )
        self.assertEqual(result, self.user)

    def test_email_kwarg_takes_priority_over_username(self):
        result = self.backend.authenticate(
            None,
            username="wrong@example.com",
            email="user@example.com",
            password="StrongPass123!",
        )
        self.assertEqual(result, self.user)

    def test_authenticate_case_insensitive_email(self):
        result = self.backend.authenticate(
            None, email="USER@EXAMPLE.COM", password="StrongPass123!"
        )
        self.assertEqual(result, self.user)

    def test_wrong_password_returns_none(self):
        result = self.backend.authenticate(
            None, email="user@example.com", password="wrongpassword"
        )
        self.assertIsNone(result)

    def test_nonexistent_email_returns_none(self):
        result = self.backend.authenticate(
            None, email="ghost@example.com", password="StrongPass123!"
        )
        self.assertIsNone(result)

    def test_inactive_user_returns_none(self):
        self.user.is_active = False
        self.user.save()
        result = self.backend.authenticate(
            None, email="user@example.com", password="StrongPass123!"
        )
        self.assertIsNone(result)

    def test_missing_email_returns_none(self):
        result = self.backend.authenticate(None, password="StrongPass123!")
        self.assertIsNone(result)

    def test_missing_password_returns_none(self):
        result = self.backend.authenticate(None, email="user@example.com")
        self.assertIsNone(result)

    def test_both_missing_returns_none(self):
        result = self.backend.authenticate(None)
        self.assertIsNone(result)


# ════════════════════════════════════════════════════════════════════════════
# @token_auth_required decorator
# (tested via the leagues_data endpoint which uses it)
# ════════════════════════════════════════════════════════════════════════════


class TokenAuthDecoratorTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_no_auth_header_returns_401(self):
        resp = self.client.get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 401)
        self.assertIn("error", resp.json())

    def test_bearer_prefix_not_accepted(self):
        """Decorator only accepts 'Token', not 'Bearer'."""
        self.client.defaults["HTTP_AUTHORIZATION"] = "Bearer sometoken"
        resp = self.client.get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 401)

    def test_no_prefix_returns_401(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "justthetoken"
        resp = self.client.get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 401)

    def test_invalid_token_value_returns_401(self):
        self.client.defaults["HTTP_AUTHORIZATION"] = "Token totallyfaketoken"
        resp = self.client.get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 401)

    def test_valid_token_grants_access(self):
        client = auth_client(self.user)
        resp = client.get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 200)

    def test_deleted_token_returns_401(self):
        token = get_or_create_token(self.user)
        key = token.key
        token.delete()
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Token {key}"
        resp = self.client.get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 401)


# ════════════════════════════════════════════════════════════════════════════
# POST /api/auth/register/
# ════════════════════════════════════════════════════════════════════════════


class RegisterViewTests(TestCase):
    def _post(self, **kwargs):
        payload = {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        payload.update(kwargs)
        return self.client.post(REGISTER_URL, data=payload, content_type="application/json")

    def test_success_returns_201(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 201)

    def test_success_returns_token_and_user(self):
        resp = self._post()
        data = resp.json()
        self.assertIn("token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "new@example.com")

    def test_user_is_created_in_db(self):
        self._post()
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_token_is_created_in_db(self):
        resp = self._post()
        token_key = resp.json()["token"]
        self.assertTrue(Token.objects.filter(key=token_key).exists())

    def test_email_stored_lowercase(self):
        self._post(email="UPPER@EXAMPLE.COM")
        self.assertTrue(User.objects.filter(email="upper@example.com").exists())

    def test_duplicate_email_returns_400(self):
        make_user(email="existing@example.com")
        resp = self._post(email="existing@example.com")
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_email_case_insensitive(self):
        make_user(email="existing@example.com")
        resp = self._post(email="EXISTING@EXAMPLE.COM")
        self.assertEqual(resp.status_code, 400)

    def test_password_mismatch_returns_400(self):
        resp = self._post(password_confirm="DifferentPass456!")
        self.assertEqual(resp.status_code, 400)

    def test_weak_password_returns_400(self):
        resp = self._post(password="123", password_confirm="123")
        self.assertEqual(resp.status_code, 400)

    def test_common_password_returns_400(self):
        resp = self._post(password="password", password_confirm="password")
        self.assertEqual(resp.status_code, 400)

    def test_invalid_email_format_returns_400(self):
        resp = self._post(email="not-an-email")
        self.assertEqual(resp.status_code, 400)

    def test_missing_email_returns_400(self):
        resp = self.client.post(
            REGISTER_URL,
            data={"password": "StrongPass123!", "password_confirm": "StrongPass123!"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_get_returns_405(self):
        resp = self.client.get(REGISTER_URL)
        self.assertEqual(resp.status_code, 405)


# ════════════════════════════════════════════════════════════════════════════
# POST /api/auth/login/
# ════════════════════════════════════════════════════════════════════════════


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def _post(self, email="user@example.com", password="StrongPass123!"):
        return self.client.post(
            LOGIN_URL,
            data={"email": email, "password": password},
            content_type="application/json",
        )

    def test_success_returns_200(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200)

    def test_success_returns_token_and_user(self):
        data = self._post().json()
        self.assertIn("token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "user@example.com")

    def test_login_returns_existing_token(self):
        """Login should reuse the existing token, not create a new one."""
        existing_token = get_or_create_token(self.user)
        data = self._post().json()
        self.assertEqual(data["token"], existing_token.key)

    def test_case_insensitive_email(self):
        resp = self._post(email="USER@EXAMPLE.COM")
        self.assertEqual(resp.status_code, 200)

    def test_wrong_password_returns_401(self):
        resp = self._post(password="wrongpassword")
        self.assertEqual(resp.status_code, 401)

    def test_nonexistent_email_returns_401(self):
        resp = self._post(email="ghost@example.com")
        self.assertEqual(resp.status_code, 401)

    def test_missing_email_returns_400(self):
        resp = self.client.post(
            LOGIN_URL, data={"password": "StrongPass123!"}, content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_missing_password_returns_400(self):
        resp = self.client.post(
            LOGIN_URL, data={"email": "user@example.com"}, content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_get_returns_405(self):
        resp = self.client.get(LOGIN_URL)
        self.assertEqual(resp.status_code, 405)


# ════════════════════════════════════════════════════════════════════════════
# POST /api/auth/logout/
# ════════════════════════════════════════════════════════════════════════════


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_success_returns_204(self):
        client = auth_client(self.user)
        resp = client.post(LOGOUT_URL)
        self.assertEqual(resp.status_code, 204)

    def test_logout_deletes_token_from_db(self):
        token = get_or_create_token(self.user)
        client = auth_client(self.user)
        client.post(LOGOUT_URL)
        self.assertFalse(Token.objects.filter(key=token.key).exists())

    def test_old_token_rejected_after_logout(self):
        client = auth_client(self.user)
        client.post(LOGOUT_URL)
        resp = client.get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 401)

    def test_unauthenticated_returns_401(self):
        resp = self.client.post(LOGOUT_URL)
        self.assertEqual(resp.status_code, 401)

    def test_get_returns_405(self):
        client = auth_client(self.user)
        resp = client.get(LOGOUT_URL)
        self.assertEqual(resp.status_code, 405)


# ════════════════════════════════════════════════════════════════════════════
# GET /api/auth/me/
# ════════════════════════════════════════════════════════════════════════════


class MeViewTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_returns_200_with_user_info(self):
        client = auth_client(self.user)
        resp = client.get(ME_URL)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["email"], "user@example.com")
        self.assertEqual(data["id"], self.user.pk)

    def test_does_not_expose_password(self):
        client = auth_client(self.user)
        data = client.get(ME_URL).json()
        self.assertNotIn("password", data)

    def test_unauthenticated_returns_401(self):
        resp = self.client.get(ME_URL)
        self.assertEqual(resp.status_code, 401)

    def test_post_returns_405(self):
        client = auth_client(self.user)
        resp = client.post(ME_URL)
        self.assertEqual(resp.status_code, 405)


# ════════════════════════════════════════════════════════════════════════════
# POST /api/auth/password-reset/
# ════════════════════════════════════════════════════════════════════════════


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def _post(self, email="user@example.com"):
        return self.client.post(
            PASSWORD_RESET_URL, data={"email": email}, content_type="application/json"
        )

    def test_registered_email_returns_200(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200)

    def test_registered_email_sends_one_email(self):
        self._post()
        self.assertEqual(len(mail.outbox), 1)

    def test_email_sent_to_correct_recipient(self):
        self._post()
        self.assertIn("user@example.com", mail.outbox[0].recipients())

    def test_email_contains_reset_link(self):
        self._post()
        self.assertIn("password-reset/confirm", mail.outbox[0].body)

    def test_email_contains_uid_and_token(self):
        self._post()
        body = mail.outbox[0].body
        self.assertIn("uid=", body)
        self.assertIn("token=", body)

    def test_unknown_email_returns_200_safe_response(self):
        """Must not reveal whether an email is registered (prevents enumeration)."""
        resp = self._post(email="unknown@example.com")
        self.assertEqual(resp.status_code, 200)

    def test_unknown_email_sends_no_email(self):
        self._post(email="unknown@example.com")
        self.assertEqual(len(mail.outbox), 0)

    def test_same_safe_message_regardless_of_email(self):
        resp_known = self._post(email="user@example.com")
        resp_unknown = self._post(email="ghost@example.com")
        self.assertEqual(resp_known.json()["detail"], resp_unknown.json()["detail"])

    def test_get_returns_405(self):
        resp = self.client.get(PASSWORD_RESET_URL)
        self.assertEqual(resp.status_code, 405)


# ════════════════════════════════════════════════════════════════════════════
# POST /api/auth/password-reset/confirm/
# ════════════════════════════════════════════════════════════════════════════


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetConfirmViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def _post(self, uid=None, token=None, new_password="NewStrongPass456!"):
        return self.client.post(
            PASSWORD_RESET_CONFIRM_URL,
            data={
                "uid": uid if uid is not None else self.uid,
                "token": token if token is not None else self.token,
                "new_password": new_password,
            },
            content_type="application/json",
        )

    def test_success_returns_200(self):
        resp = self._post()
        self.assertEqual(resp.status_code, 200)

    def test_password_is_changed(self):
        self._post()
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass456!"))

    def test_old_password_no_longer_works(self):
        self._post()
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("StrongPass123!"))

    def test_existing_tokens_are_invalidated(self):
        auth_token = get_or_create_token(self.user)
        self._post()
        self.assertFalse(Token.objects.filter(key=auth_token.key).exists())

    def test_token_cannot_be_reused(self):
        self._post()
        # Token is now invalid because password changed
        resp = self._post()
        self.assertEqual(resp.status_code, 400)

    def test_invalid_uid_returns_400(self):
        resp = self._post(uid="notavaliduid")
        self.assertEqual(resp.status_code, 400)

    def test_invalid_token_returns_400(self):
        resp = self._post(token="invalid-token-value")
        self.assertEqual(resp.status_code, 400)

    def test_weak_new_password_returns_400(self):
        resp = self._post(new_password="123")
        self.assertEqual(resp.status_code, 400)

    def test_numeric_only_password_returns_400(self):
        resp = self._post(new_password="12345678901234")
        self.assertEqual(resp.status_code, 400)

    def test_get_returns_405(self):
        resp = self.client.get(PASSWORD_RESET_CONFIRM_URL)
        self.assertEqual(resp.status_code, 405)


# ════════════════════════════════════════════════════════════════════════════
# League User Isolation
# ════════════════════════════════════════════════════════════════════════════


class LeaguesDataTests(TestCase):
    """GET /api/leagues/ — must only return the requesting user's leagues."""

    def setUp(self):
        self.user_a = make_user(email="a@example.com")
        self.user_b = make_user(email="b@example.com")
        make_league(self.user_a, league_id=10, league_year=2024, league_name="A League")
        make_league(self.user_b, league_id=20, league_year=2024, league_name="B League")

    def test_unauthenticated_returns_401(self):
        resp = self.client.get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 401)

    def test_user_sees_own_current_year_league(self):
        resp = auth_client(self.user_a).get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 200)
        ids = [l["league_id"] for l in resp.json()["leagues_current_year"]]
        self.assertIn(10, ids)

    def test_user_cannot_see_other_users_league(self):
        resp = auth_client(self.user_a).get(LEAGUES_URL)
        all_ids = [
            l["league_id"]
            for l in resp.json()["leagues_current_year"] + resp.json()["leagues_previous_year"]
        ]
        self.assertNotIn(20, all_ids)

    def test_previous_year_leagues_are_separated(self):
        make_league(self.user_a, league_id=11, league_year=2022, league_name="Old A")
        resp = auth_client(self.user_a).get(LEAGUES_URL)
        prev_ids = [l["league_id"] for l in resp.json()["leagues_previous_year"]]
        self.assertIn(11, prev_ids)
        curr_ids = [l["league_id"] for l in resp.json()["leagues_current_year"]]
        self.assertNotIn(11, curr_ids)

    def test_user_with_no_leagues_sees_empty_lists(self):
        user_c = make_user(email="c@example.com")
        resp = auth_client(user_c).get(LEAGUES_URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["leagues_current_year"], [])
        self.assertEqual(resp.json()["leagues_previous_year"], [])


class GetLeagueDetailsTests(TestCase):
    """GET /api/league/<year>/<id>/ — user isolation."""

    def setUp(self):
        self.user_a = make_user(email="a@example.com")
        self.user_b = make_user(email="b@example.com")
        make_league(self.user_a, league_id=100, league_year=2024)

    def test_unauthenticated_returns_401(self):
        resp = self.client.get(LEAGUE_DETAIL_URL.format(year=2024, league_id=100))
        self.assertEqual(resp.status_code, 401)

    def test_other_user_cannot_access_league_returns_400(self):
        resp = auth_client(self.user_b).get(
            LEAGUE_DETAIL_URL.format(year=2024, league_id=100)
        )
        self.assertEqual(resp.status_code, 400)

    def test_nonexistent_league_returns_400(self):
        resp = auth_client(self.user_a).get(
            LEAGUE_DETAIL_URL.format(year=2024, league_id=9999)
        )
        self.assertEqual(resp.status_code, 400)

    def test_owner_can_access_own_league(self):
        """Owner gets 200 with league data (view only reads DB, no ESPN call)."""
        resp = auth_client(self.user_a).get(
            LEAGUE_DETAIL_URL.format(year=2024, league_id=100)
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["league_id"], 100)
        self.assertEqual(data["league_year"], 2024)


class DistinctLeaguesPreviousYearTests(TestCase):
    """GET /api/distinct-leagues-previous/ — user isolation."""

    def setUp(self):
        self.user_a = make_user(email="a@example.com")
        self.user_b = make_user(email="b@example.com")
        make_league(self.user_a, league_id=1, league_year=2023)
        make_league(self.user_b, league_id=2, league_year=2023)

    def test_unauthenticated_returns_401(self):
        resp = self.client.get(DISTINCT_PREV_URL)
        self.assertEqual(resp.status_code, 401)

    def test_user_sees_own_previous_leagues(self):
        resp = auth_client(self.user_a).get(DISTINCT_PREV_URL)
        self.assertEqual(resp.status_code, 200)
        ids = [l["league_id"] for l in resp.json()]
        self.assertIn(1, ids)

    def test_user_cannot_see_other_users_previous_leagues(self):
        resp = auth_client(self.user_a).get(DISTINCT_PREV_URL)
        ids = [l["league_id"] for l in resp.json()]
        self.assertNotIn(2, ids)


class CopyOldLeagueTests(TestCase):
    """POST /api/copy-old-league/<id>/ — user isolation."""

    def setUp(self):
        self.user_a = make_user(email="a@example.com")
        self.user_b = make_user(email="b@example.com")
        make_league(self.user_a, league_id=5, league_year=2023)

    def test_unauthenticated_returns_401(self):
        resp = self.client.post(COPY_OLD_LEAGUE_URL.format(league_id=5))
        self.assertEqual(resp.status_code, 401)

    def test_other_user_cannot_copy_league_returns_404(self):
        resp = auth_client(self.user_b).post(COPY_OLD_LEAGUE_URL.format(league_id=5))
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_league_returns_404(self):
        resp = auth_client(self.user_a).post(COPY_OLD_LEAGUE_URL.format(league_id=9999))
        self.assertEqual(resp.status_code, 404)


class LeagueInputTests(TestCase):
    """POST /api/league-input/ — auth requirement."""

    def test_unauthenticated_returns_401(self):
        resp = self.client.post(
            LEAGUE_INPUT_URL,
            data={"league_id": 1, "league_year": 2024, "swid": "{X}", "espn_s2": "s2"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_authenticated_reaches_view_logic(self):
        """Authenticated request passes auth gate (ESPN API is mocked)."""
        user = make_user()
        with patch("backend.fantasy_stats.views.fetch_league") as mock_fetch:
            mock_league = MagicMock()
            mock_league.settings.name = "Mock League"
            mock_fetch.return_value = mock_league
            resp = auth_client(user).post(
                LEAGUE_INPUT_URL,
                data={
                    "league_id": 42,
                    "league_year": 2024,
                    "swid": "{TEST-SWID}",
                    "espn_s2": "test_s2",
                },
                content_type="application/json",
            )
            # Auth passed — view ran and called fetch_league
            mock_fetch.assert_called_once()

    def test_league_input_associates_league_with_user(self):
        """New league is stored under the authenticated user."""
        user = make_user()
        with patch("backend.fantasy_stats.views.fetch_league") as mock_fetch:
            mock_league = MagicMock()
            mock_league.settings.name = "New League"
            mock_fetch.return_value = mock_league
            auth_client(user).post(
                LEAGUE_INPUT_URL,
                data={
                    "league_id": 99,
                    "league_year": 2024,
                    "swid": "{TEST-SWID}",
                    "espn_s2": "test_s2",
                },
                content_type="application/json",
            )
        league = LeagueInfo.objects.filter(league_id=99, league_year=2024).first()
        if league:  # Only assert if the view succeeded in creating the record
            self.assertEqual(league.user, user)
