GAME_VERSION = "1.1.0"
OLD_VERSION = "1.0.0.21184"
NEW_VERSION = GAME_VERSION
VERSION = GAME_VERSION

PATCH_VERSION = "1.6.0"


def visualize_whitespace(text: str):
    return text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def inline_whitespace(text: str):
    return text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')