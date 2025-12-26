GAME_VERSION = "1.2.0.23023"
OLD_VERSION = "1.1.0"
NEW_VERSION = GAME_VERSION
VERSION = GAME_VERSION

PATCH_VERSION = "1.7.0"


def visualize_whitespace(text: str):
    return text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def inline_whitespace(text: str):
    return text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')