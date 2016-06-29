# mycroft-skill-podcast
My 3rd attempt at creating a mycroft skill.

This is a 3rd party skill that can either reside in `~/.mycroft/third_party_skills/` or `/opt/mycroft/third_party` .

This skill is based on the [Jupiter Broadcasting Skill](https://github.com/the7erm/mycroft-skill-jupiter-broadcasting).

# Intents
| Intent               | Example Keyphrase                                         | Function                                                    | Output       |
|----------------------|-----------------------------------------------------------|-------------------------------------------------------------|--------------|
| PodcastListenIntent  | Mycroft, play the latest Security Now Episode podcast     | Play the latest episode of a podcast                        | opening .... |
| PodcastLatestIntent  | Mycroft, latest Linux Action Show netcast                 | Visit the latest episode page                               | opening .... |
| PodcastLatestIntent  | Mycroft, open Tech Snap Podcast Site                      | Visit the main page for the podcast                         | opening .... |


## Install
```
mkdir -p ~/.mycroft/third_party_skills/
cd ~/.mycroft/third_party_skills/
git clone https://github.com/the7erm/mycroft-skill-podcast.git podcast
```

## Configuring `mycroft.ini`
By default the `PodcastSkill` uses `xdg-open` to open media & webpages.
Everyone has their favorite media player feel free to set it to `vlc` please
note `vlc --flag` will not work.  You'll need to write a wrapper script that
calls `vlc` with the command line arguments you'd like.

```ini
[PodcastSkill]
# Media player you want the PodcastSkill to use
media_command = "xdg-open"
# Browser you'd like the PodcastSkill to use
webpage_command = "xdg-open"
```

## `feeds.json`
`feeds.json` resides in `~/.mycroft/skills/PodcastSkill`
For your initial setup you just need to set the `rss_url` field.  The
`PodcastSkill` will then generate additional fields based on data from the
rss feed.

# Example `feeds.json`
```json
{
    "Coder Radio": {
        "rss_url": "http://feeds.feedburner.com/coderradiovideo"
    },
    "Linux Action Show": {
        "rss_url": "http://feeds.feedburner.com/computeractionshowvideo"
    },
    "Security Now": {
        "rss_url": "http://feeds.twit.tv/sn_video_hd.xml"
    },
    "TechSnap": {
        "rss_url": "http://feeds.feedburner.com/techsnaphd"
    }
}
```

After you `./mycroft.sh restart` the `feeds.json` file will be altered.
The `keyphrase` section is now present, this is a list of all the values mycoft
will listen for when identifying the show you wan to listen to.  You can add
your own `keyphrases`. Take a look at `TechSnap`'s phrases.  It'd be a good
idea to add `tech snap` and if you slur your words `text app`, `texas app` and even
`texts app`.  Perhaps in the future the rss spec will adapt a phonetic list,
but at this point in time there is no such spec that I'm aware of.

During testing mycroft was reporting:
```json
    ["tech snap", "tech snapped", "techsnap", "texas map", "text app",
     "text nap", "text snapped", "texts snapped"]
```

Also you can include your own alternate pronunciations.  EG: `LAS`, `L.A.S.`,
`Lass` and `Last` would be great for the `Linux Action Show`.

# Example `feeds.json` after run
```json
{
    "Coder Radio": {
        "keyphrases": [
            "coder radio",
            "coder radio video"
        ],
        "rss_url": "http://feeds.feedburner.com/coderradiovideo",
        "title": "Coder Radio Video"
    },
    "Linux Action Show": {
        "href": "http://www.jupiterbroadcasting.com",
        "keyphrases": [
            "linux action show",
            "the linux action show! video"
        ],
        "rss_url": "http://feeds.feedburner.com/computeractionshowvideo",
        "title": "The Linux Action Show! Video"
    },
    "Security Now": {
        "keyphrases": [
            "security now",
            "security now (video-hd)"
        ],
        "rss_url": "http://feeds.twit.tv/sn_video_hd.xml",
        "title": "Security Now (Video-HD)"
    },
    "TechSnap": {
        "href": "http://www.jupiterbroadcasting.com",
        "keyphrases": [
            "techsnap",
            "techsnap in hd"
        ],
        "rss_url": "http://feeds.feedburner.com/techsnaphd"
    }
}
```

## feedcache
The PodcastSkill will only fetch a podcast once per hour.
`~/.mycroft/skills/PodcastSkill/feedcache` is the location of the cache file.

