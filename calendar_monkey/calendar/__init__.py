import msal
import logging
from requests_oauthlib import OAuth2Session
from calendar_monkey.calendar.exceptions import (
    CalendarLoginException,
    CalendarException,
)
import urllib.parse
import datetime
import random
import pytz
import json
import dateutil.parser
from msal_extensions.persistence import FilePersistence
from msal_extensions import PersistedTokenCache


def create_cache(path):
    return PersistedTokenCache(FilePersistence(path))


# https://docs.microsoft.com/en-us/graph/api/resources/calendar?view=graph-rest-beta


class CalendarApi(object):
    def __init__(self, config, cache, timezone):
        self.__app = msal.PublicClientApplication(
            config.client_id, authority=config.authority, token_cache=cache, timeout=5
        )
        self.__config = config
        self.graph_url = "https://graph.microsoft.com/beta"
        self.__log = logging.getLogger(__name__)
        self.__graph_client = None
        self.__token = None
        self.__chosen_account = None
        self.__timezone = timezone

    def validate(self, username=None):
        result = None

        accounts = self.__app.get_accounts(username)

        if accounts:
            self.__log.info(
                "Account(s) exists in cache, probably with token too. Let's try."
            )
            self.__chosen_account = accounts[0]
            self.__log.info(
                "Proceed with account: %s" % self.__chosen_account["username"]
            )
            # Now let's try to find a token in cache for this account
            result = self.__app.acquire_token_silent(
                self.__config["scope"], account=self.__chosen_account
            )
        if result:
            self.__create_client(token=result)

        return result

    @property
    def chosen_account(self):
        return self.__chosen_account

    def __create_client(self, token):
        self.__graph_client = OAuth2Session(token=token)
        self.__token = token

    @property
    def token(self):
        return self.__token

    def valid(self):
        return self.__token is not None

    def _build_auth_code_flow(self, scopes, redirect_uri):
        return self.__app.initiate_auth_code_flow(scopes, redirect_uri)

    def _acquire_token_by_auth_code_flow(self, flow, args):
        result = self.__app.acquire_token_by_auth_code_flow(flow, args)

        if "error" in result:
            raise CalendarLoginException(
                "unable to login: %s(%s)"
                % (result.get("error"), result.get("error_description"))
            )

        self.__create_client(token=result)

    def login(self):
        result = self.validate()

        if not result:
            self.__log.info(
                "No suitable token exists in cache. Let's get a new one from AAD."
            )
            result = self.__app.acquire_token_by_username_password(
                self.__config.username, self.__config.password, self.__config.scope
            )

            if "error" in result:
                raise CalendarLoginException(
                    "unable to login: %s(%s)"
                    % (result.get("error"), result.get("error_description"))
                )

            self.__graph_client = OAuth2Session(token=result)

    def me(self):
        resp = self.__graph_client.get("{0}/me".format(self.graph_url))

        if resp.status_code != 200:
            raise CalendarException("invalid: %s %s" % (resp.status_code, resp.json()))

        return resp.json()

    def get_events(self, start, end):
        params = {
            "startDateTime": "%s" % (start.isoformat()),
            "endDateTime": "%s" % (end.isoformat()),
            "$select": "id,start,subject",
        }

        link = "{0}/me/calendar/calendarView?{1}".format(
            self.graph_url, urllib.parse.urlencode(params)
        )

        while True:
            events_resp = self.__graph_client.get(link)
            if events_resp.status_code != 200:
                raise Exception(
                    "invalid: %s %s" % (events_resp.status_code, events_resp.json())
                )

            return events_resp.json()["value"]

    def cancel_event(self, event, dry_run=False):
        (id, subject, start, tz) = (
            event["id"],
            event["subject"],
            dateutil.parser.isoparse(event["start"]["dateTime"]),
            pytz.timezone(event["start"]["timeZone"]),
        )
        self.__log.info(
            "Cancel event : %s at %s (id = %s)"
            % (
                subject,
                start.replace(tzinfo=tz).astimezone(pytz.timezone(self.__timezone)),
                id,
            )
        )
        delete_ep = "{0}/me/events/{1}".format(self.graph_url, id)

        if not (dry_run):
            delete_resp = self.__graph_client.delete(delete_ep)
            if delete_resp.status_code != 204:
                raise Exception(
                    "invalid: %s %s" % (delete_resp.status_code, delete_resp.json())
                )
        # cancel_ep = '{0}/me/events/{1}/cancel'.format(self.graph_url, id)
        # cancel_resp = self.__graph_client.post(cancel_ep, json={'comment':'🤨'})
        # if not(dry_run):
        #    ## 🐒
        #    if cancel_resp.status_code != 200:
        #        raise Exception('invalid: %s %s' %
        #                        (cancel_resp.status_code, cancel_resp.json()))

    def cancel(self, days_offset=0, days=7, num_entries=1, dry_run=False):
        tz = pytz.timezone(self.__timezone)
        now = tz.localize(datetime.datetime.now())

        start = now + datetime.timedelta(days_offset)
        end = now + datetime.timedelta(days_offset + days)

        events = self.get_events(start, end)
        cnt = min(len(events), num_entries)
        i = 0
        while i < cnt:
            event = random.choice(events)
            self.cancel_event(event, dry_run)
            i = i + 1
        return cnt

    def health(self):
        if not self.validate():
            self.__log.exception("no login")
            return False
        try:
            self.me()
        except Exception:
            self.__log.exception("healthcheck failed")
            return False

        return True
