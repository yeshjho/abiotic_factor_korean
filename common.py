GAME_VERSION = "0.10.0.15580"
OLD_VERSION = "0.10.0.15214"
NEW_VERSION = GAME_VERSION
VERSION = GAME_VERSION

PATCH_VERSION = "1.3.0"


def visualize_whitespace(text: str):
    return text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def inline_whitespace(text: str):
    return text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')