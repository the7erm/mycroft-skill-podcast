# Copyright 2016 Eugene R. Miller
#
# Mycroft Podcast skill is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Mycroft Podcast is distributed in the hope that it will
#  be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Podcast skill.
# If not, see <http://www.gnu.org/licenses/>.

from os.path import dirname, join, expanduser, exists
from adapt.intent import IntentBuilder
from adapt.tools.text.tokenizer import EnglishTokenizer
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

from feedcache import cache
from pprint import pprint, pformat
from copy import deepcopy

import subprocess
import shelve
import json

__author__ = 'the7erm'

LOGGER = getLogger(__name__)

class FeedReader(object):
    def __init__(self, feed_filename, storage_path):
        super(FeedReader, self).__init__()
        self.ttl = 60 * 60 # 60 minutes
        self.feeds = {}
        self.feed_filename = feed_filename
        self.storage_path = storage_path
        self.errors = []

    def exists(self):
        return exists(self.feed_filename)

    def load_shows(self):
        if not self.exists():
            self.errors.append({
                "dialog": "missing.feeds.json",
                "data": {}
            })
            return self

        with open(self.feed_filename, "r") as fp:
            try:
                self.feeds = json.loads(fp.read())
            except ValueError as e:
                self.errors.append({
                    "dialog": "error.reading.feeds.json",
                    "data": {
                        "error": "%s" % e
                    }
                })
                return self

        self.set_rss_feed_keyphrases()
        self.save()
        return self

    def set_rss_feed_keyphrases(self):
        for key_title, feed in self.feeds.items():
            title, href = self.get_feed_data(feed)
            keyphrases = feed.get("keyphrases", [])
            self.append_keyphrases(key_title, keyphrases)
            self.append_keyphrases(title, keyphrases)
            keyphrases.sort()
            feed['keyphrases'] = keyphrases
            feed['href'] = href
            feed['title'] = title

    def get_feed_data(self, feed, ttl=None):
        # This fetches the feed and gets the title from the rss feed itself.
        if ttl is None:
            ttl = self.ttl

        storage = shelve.open(self.storage_path)
        title = None
        href = None
        rss_url = feed.get("rss_url")
        if not rss_url:
            self.errors.append({
                "dialog": "empty.rss.url",
                "data": feed
            })
            return title, href

        try:
            fc = cache.Cache(storage, timeToLiveSeconds=ttl)
            parsed_data = fc.fetch(rss_url)
            if parsed_data.feed.title:
                title = parsed_data.feed.title
            if parsed_data.feed.link:
                href = parsed_data.feed.link
        finally:
            storage.close()

        return title, href

    def append_keyphrases(self, keyphrase, keyphrases):
        if not keyphrase:
            return

        keyphrase = keyphrase.strip()
        if not keyphrase:
            return

        lower_kp = keyphrase.lower()
        if lower_kp not in keyphrases:
            keyphrases.append(lower_kp)

    def get_latest_episode(self, feed, ttl=None):
        storage = shelve.open(self.storage_path)
        latest_entry = None

        if ttl is None:
            ttl = self.ttl

        try:
            fc = cache.Cache(storage, timeToLiveSeconds=ttl)
            parsed_data = fc.fetch(feed["rss_url"])
            # print "parsed_data.feed.title:", parsed_data.feed.title
            for entry in parsed_data.entries:
                latest_entry = entry
                break
        finally:
            storage.close()

        if latest_entry is None:
            self.errors.append({
                "dialog": "no.latest.episode",
                "data": {
                    "feed": feed
                }
            })
        return latest_entry

    def save(self):
        with open(self.feed_filename, "w") as fp:
            fp.write(json.dumps(self.feeds, sort_keys=True,
                                indent=4, separators=(',', ': ')))
        return self


class PodcastSkill(MycroftSkill):

    def __init__(self):
        super(PodcastSkill, self).__init__(name="PodcastSkill")

    def initialize(self):
        self.showmap = {}
        self.feed_reader = FeedReader(
            join(self.file_system.path, "feeds.json"),
            join(self.file_system.path, 'feedcache')
        )
        self.load_data_files(dirname(__file__))
        self.load_regex_files(join(dirname(__file__), 'regex', self.lang))
        self.load_shows()

        tokenizer = EnglishTokenizer()
        self.tokenize_shows(tokenizer)

        listen_intent = IntentBuilder(
            "PodcastListenIntent").require("PodcastKeyword").require(
                "PlayKeyword").require(
                "LatestKeyword").require("Podcast").build()

        self.register_intent(listen_intent, self.handle_listen_intent)

        latest_intent = IntentBuilder(
            "PodcastLatestIntent").require("PodcastKeyword").require(
                "LatestKeyword").require(
                "Podcast").build()

        self.register_intent(latest_intent, self.handle_latest_intent)

        open_intent = IntentBuilder(
            "PodcastOpenIntent").require("PodcastKeyword").require(
                "OpenKeyword").require(
                "Podcast").build()

        self.register_intent(open_intent, self.handle_open_intent)

    def load_shows(self):
        self.feed_reader.load_shows()
        self.say_errors()

    def say_errors(self):
        while self.feed_reader.errors:
            error = self.feed_reader.errors.pop(0)
            self.speak_dialog(error.get("dialog"), error.get("data"))

    def tokenize_show(self, tokenizer, phrase, entry):
        tokenized_phrase = tokenizer.tokenize(phrase)[0]
        self.add_token(phrase, entry)

        if phrase != tokenized_phrase:
            self.add_token(tokenized_phrase, entry)

    def add_token(self, token, entry):
        self.register_vocabulary(token, "Podcast")
        if token in self.showmap:
            self.showmap[token] += entry
        else:
            self.showmap[token] = entry

    def tokenize_shows(self, tokenizer):
        for key_title, feed in self.feed_reader.feeds.items():
            entry = [key_title]
            self.tokenize_show(tokenizer, key_title, entry)
            for phrase in feed.get("keyphrases", []):
                entry = [feed]
                self.tokenize_show(tokenizer, phrase, entry)

    def latest_show(self, message, media=False):
        show_name = message.metadata.get('Podcast')
        entries = self.showmap.get(show_name)
        LOGGER.debug("message:%s" % message)
        LOGGER.debug("latest entries:%s" % entries)

        if entries and len(entries) > 0:
            feed = entries[0]
            LOGGER.debug("feed:%s" % feed)
            data = {
                "stream": "%s" % feed.get("title", "")
            }
            self.speak_dialog("opening.latest", data)
            episode = self.feed_reader.get_latest_episode(feed)
            if episode:
                # Set default to the whatever the page's link is.
                link = feed['href']
                open_cmd = self.config.get("webpage_command", "xdg-open")

                if hasattr(episode, 'media_content') and \
                   episode.media_content:
                        # This episode has media content.
                        # In some cases people set the media_content
                        # to the same as the `link`.
                        # The `link` should be a webpage with show notes
                        # And the media_content should be the url to
                        # listen to or watch the episode.
                        if media:
                            # We're supposed to get the media url.
                            link = episode.media_content
                            open_cmd = self.config.get("media_command",
                                                       open_cmd)
                        elif episode.media_content != episode.link:
                            # The media_content url is not the same
                            # so it's a webpage, for that episode.
                            link = episode.link
                else:
                    link = episode.link

                cmd = [open_cmd, link]
                subprocess.check_output(cmd)
                LOGGER.debug("episode:%s" % pformat(episode))
        self.say_errors()


    def handle_latest_intent(self, message):
        self.latest_show(message, False)

    def handle_listen_intent(self, message):
        self.latest_show(message, True)

    def handle_open_intent(self, message):
        show_name = message.metadata.get('Podcast')
        entries = self.showmap.get(show_name)
        LOGGER.debug("message:%s" % message)

        if entries and len(entries) > 0:
            entry = entries[0]
            LOGGER.debug("entry:%s" % entry)
            data = {
                "stream": "%s website" % entry.get("title", "")
            }
            self.speak_dialog("opening", data)
            subprocess.check_output(['xdg-open', entry.get("href")])

    def stop(self):
        pass


def create_skill():
    return PodcastSkill()
