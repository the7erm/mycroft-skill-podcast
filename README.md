# mycroft-skill-podcast
My 3rd attempt at creating a mycroft skill

This is a 3rd party skill that can either reside in `~/.mycroft/third_party_skills/` or `/opt/mycroft/third_party` .

This skill requires a specific pull request to be merged.  https://github.com/MycroftAI/mycroft-core/pull/222 at this point in time it's still not merged.  This code may be altered.

This skill is based on the [Jupiter Broadcasting Skill](https://github.com/the7erm/mycroft-skill-jupiter-broadcasting).

# Intents
| Intent         | Example Keyphrase                                         | Function                                                    | Output                                                                                                            |
|----------------|-----------------------------------------------------------|-------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
|                | Mycroft,                                                  |                                                             |                                                                                                  |

## Install
```
mkdir -p ~/.mycroft/third_party_skills/
cd ~/.mycroft/third_party_skills/
git clone https://github.com/the7erm/mycroft-skill-podcast.git podcast
# restart the skills service
# usually
./mycroft.sh restart
```

