"""Reports that Rock-Paper-Scissors-2D was used to the trace service, and nothing else.

What is sent: the program's name (``Rock-Paper-Scissors-2D``) and version with a ``startup``
event, and a round-played event (tag result: win, lose or tie) after each round. Nothing about you, your machine or your choices.

Reporting is on by default. The first launch writes a ``usage_reporting``
block to ``settings.json`` and prints a one-line notice saying so and how to
turn it off; setting ``enabled`` to ``false`` there does. So do the
``TRACE_USAGE_REPORTING=off`` and ``DO_NOT_TRACK=1`` environment variables,
which every trace client honours and which win over the settings file because
the client checks them first. Every call returns immediately and never raises:
the network happens on a daemon thread owned by the vendored client in
``trace_client.py``. Details: https://github.com/Stephenson-Software/trace#usage-reporting
"""
import atexit
import json
import os

from trace_client import TraceClient, environment_opts_out

# @author Daniel McCoy Stephenson
# @since September 24th, 2026

APPLICATION = "Rock-Paper-Scissors-2D"
SETTINGS_SECTION = "usage_reporting"
DEFAULT_ENDPOINT = "https://trace.danielstephenson.dev"
# The program key Rock-Paper-Scissors-2D ships with. Keys identify a program rather than
# guard anything (trace's ADR 0001), so it is kept here in the open.
DEFAULT_KEY = "xFiLeIXEsFq-fkmX5Sa8ia3E3h8p2xgRtY-raSSYqTE"
VERSION = "0.1"

_HERE = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.normpath(os.path.join(_HERE, "..", "settings.json"))

DETAILS_URL = "https://github.com/Stephenson-Software/trace#usage-reporting"

FIRST_RUN_NOTICE = (
    "Usage reporting is on: Rock-Paper-Scissors-2D sends its name and version at startup and a round-played event with each round's result to "
    "https://trace.danielstephenson.dev - nothing about you, your machine or your choices. "
    'Turn it off with "usage_reporting": {"enabled": false} in settings.json, or for every '
    "trace-reporting program with the environment variable TRACE_USAGE_REPORTING=off. "
    "Details: " + DETAILS_URL
)

# Shown on the first launch instead when TRACE_USAGE_REPORTING=off or DO_NOT_TRACK=1 is
# already set: the settings block is still written, but saying reporting is on would mislead.
FIRST_RUN_NOTICE_OFF_BY_ENVIRONMENT = "Usage reporting is off (environment). Details: " + DETAILS_URL


def firstRunNotice():
    """The line the first launch prints: FIRST_RUN_NOTICE, unless the environment has opted out."""
    if environment_opts_out():
        return FIRST_RUN_NOTICE_OFF_BY_ENVIRONMENT
    return FIRST_RUN_NOTICE


def defaultSettings():
    """The usage_reporting block written to the settings file on the first launch."""
    return {"enabled": True, "endpoint": DEFAULT_ENDPOINT, "key": DEFAULT_KEY}


def loadSettings(settingsFile=SETTINGS_FILE, log=print):
    """Read the usage_reporting block from the settings file, writing the default block
    (and printing the one-time notice) when the file does not have one yet.

    Returns the usage_reporting settings, or None if the settings file exists but cannot be
    read, in which case nothing is reported and the file is left alone.
    """
    settings = {}
    if os.path.exists(settingsFile):
        try:
            with open(settingsFile, "r") as f:
                settings = json.load(f)
            if not isinstance(settings, dict):
                raise ValueError("settings file is not a JSON object")
        except (OSError, ValueError) as e:
            log("Could not read %s (%s); usage reporting is off until it is fixed." % (settingsFile, e))
            return None

    section = settings.get(SETTINGS_SECTION)
    if isinstance(section, dict):
        return section

    settings[SETTINGS_SECTION] = defaultSettings()
    log(firstRunNotice())
    try:
        with open(settingsFile, "w") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
    except OSError as e:
        log("Could not write %s (%s); the notice above will be shown again next time." % (settingsFile, e))
    return settings[SETTINGS_SECTION]


def buildClient(section):
    """A TraceClient for the given usage_reporting settings; disabled when they are None.

    Always built through the client's constructor otherwise, which puts
    TRACE_USAGE_REPORTING / DO_NOT_TRACK ahead of ``enabled`` and records why it is off in
    ``disabled_reason``. A missing endpoint or key falls back to the shipped default.
    """
    if section is None:
        return TraceClient.disabled()
    try:
        return TraceClient(
            str(section.get("endpoint") or DEFAULT_ENDPOINT),
            APPLICATION,
            key=str(section.get("key") or DEFAULT_KEY),
            enabled=bool(section.get("enabled", True)),
        )
    except Exception:
        return TraceClient.disabled()


def startUsageReporting(settingsFile=SETTINGS_FILE, log=print):
    """Read the settings, build the client and report the startup event.

    Never raises; the client is closed (sending what is queued, bounded by its timeout)
    when the interpreter exits. Returns the client so further events can be reported.
    """
    try:
        client = buildClient(loadSettings(settingsFile, log))
    except Exception:
        return TraceClient.disabled()
    client.report("startup", tags={"version": VERSION})
    atexit.register(client.close)
    return client
