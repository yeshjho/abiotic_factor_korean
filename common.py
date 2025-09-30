GAME_VERSION = "1.0.0.21184"
OLD_VERSION = "1.0.0.21035"
NEW_VERSION = GAME_VERSION
VERSION = GAME_VERSION

PATCH_VERSION = "1.5.2"


def visualize_whitespace(text: str):
    return text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def inline_whitespace(text: str):
    return text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')