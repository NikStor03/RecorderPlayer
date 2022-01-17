import gettext
import os
from typing import Optional
from database.tools import Languages


def _(text: str, language: Optional[Languages] = None) -> str:
    translate = gettext.translation(
        'translation',
        f"{os.getcwd()}/translation/locale",
        fallback=True,
        languages=[str(language)]
    )
    translate.install()
    return translate.gettext(text)
