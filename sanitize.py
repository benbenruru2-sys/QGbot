#Yes this is vibe coded, but i am way to lazy to make a sanitizing function myself (all the other code isn't vibe coded tho)

import discord

def sanitize(text: str) -> str:
    """
    Sanitize text to prevent unwanted Discord mentions,
    markdown formatting, and common dangerous strings.

    The sanitizer repeatedly processes the text until a complete
    pass makes no further changes.
    """

    if not isinstance(text, str):
        return ""

    # Strings replaced with something else.
    REPLACE_MAP = {
        "@everyone": "@\u200beveryone",
        "@here": "@\u200bhere",
    }

    # Strings stripped entirely (case-insensitive).
    STRIP_LIST = [
        # JSON / quote breaking
        '"', "{", "}", "[", "]", "'", "\\",

        # Python code execution
        "exec(",
        "eval(",
        "compile(",
        "__import__",
        "chr(",
        "globals(",
        "locals(",
        "vars(",
        "dir(",
        "os.",
        "sys.",
        "subprocess.",
        "shutil.",
        "socket.",
        "threading.",
        "multiprocessing.",
        "import",
        "input(",
        "open(",
        "ctypes.",
        "getattr(",
        "setattr(",
        "__class__",
        "__base__",
        "__subclasses__",
        "__globals__",
        "__builtins__",
        "__bases__",
        '("',
        "('",
        '")',
        "')",

        # Shell / OS commands
        "rm -rf ",
        "rm -rf ~",
        "sudo ",
        "chmod ",
        "chown ",
        "mkfs",
        "dd if=",
        "wget ",
        "curl ",
        ":(){:|:&};:",
        "> /dev/",
        "< /dev/",
        "/etc/passwd",
        "/etc/shadow",

        # Path traversal
        "../",
        "..\\",
        "%2e%2e%2f",
        "%2e%2e/",

        # Unicode abuse
        "\u202e",

        # Environment / secrets probing
        "os.environ",
        "getenv(",
        "process.env",
        ".env",

        # Script / markup injection
        "<script",
        "</script>",
        "javascript:",
        "onerror=",
        "onload=",
    ]

    # Longest strings first.
    # This prevents a shorter entry from interfering with a longer one.
    STRIP_LIST.sort(key=len, reverse=True)

    while True:
        original = text

        #Remove forbidden strings, case-insensitively.
        lower_text = text.lower()

        for forbidden in STRIP_LIST:
            forbidden_lower = forbidden.lower()

            while True:
                index = lower_text.find(forbidden_lower)

                if index == -1:
                    break
                end = index + len(forbidden)

                text = text[:index] + text[end:]
                lower_text = text.lower()

        #Escape Discord mentions.
        text = discord.utils.escape_mentions(text)

        #Apply the explicit @everyone / @here replacements.
        for old, new in REPLACE_MAP.items():
            text = text.replace(old, new)

        # 4. Escape Discord markdown.
        text = discord.utils.escape_markdown(text)

        # 5. Stop when this entire pass changed nothing.
        if text == original:
            break

    return text

if __name__ == "__main__":
    while True:
        user_input = input("Entrez du texte à assainir (ou 'exit' pour quitter) : ")
        if user_input.lower() == 'exit':
            break
        sanitized_text = sanitize(user_input)
        print(f"Texte assaini : {sanitized_text}")
        print("execution du code assaini :")
        try:
            exec(sanitized_text)
        except Exception as e:
            print(f"Erreur lors de l'exécution du code assaini : {e}")
