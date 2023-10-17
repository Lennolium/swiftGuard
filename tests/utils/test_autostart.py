import os

from swiftguard.const import USER_HOME
from swiftguard.utils.autostart import add_autostart, del_autostart


############################################
#             add_autostart()              #
############################################


def test_add_autostart_macos():
    os.environ["CURRENT_PLATFORM"] = "DARWIN"
    result = add_autostart()
    assert result is True
    launch_agent_dest = (
        f"{USER_HOME}/Library/LaunchAgents/dev.lennolium.swiftguard.plist"
    )
    assert os.path.isfile(launch_agent_dest) is True


############################################
#             del_autostart()              #
############################################


def test_del_autostart_macos():
    os.environ["CURRENT_PLATFORM"] = "DARWIN"
    del_autostart()
    launch_agent_dest = (
        f"{USER_HOME}/Library/LaunchAgents/dev.lennolium.swiftguard.plist"
    )
    assert os.path.isfile(launch_agent_dest) is False


############################################
#             add_autostart()              #
############################################


def test_add_autostart_linux():
    os.environ["CURRENT_PLATFORM"] = "LINUX"
    try:
        add_autostart()
    except NotImplementedError as e:
        assert str(e) == "Linux-support is still work in progress."


############################################
#             del_autostart()              #
############################################


def test_del_autostart_linux():
    os.environ["CURRENT_PLATFORM"] = "LINUX"
    try:
        del_autostart()
    except NotImplementedError as e:
        assert str(e) == "Linux-support is still work in progress."
