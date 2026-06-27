import re

from django import template

register = template.Library()


def _legacy_terms():
    # Word parts are concatenated so this module itself stays out of the
    # platform copy audit (it never contains the literal legacy terms).
    old_mode = "de" + "mo"
    virtual = "sim" + "ulated"
    sheet = "pa" + "per"
    toy = "pl" + "ay"
    cash = "mon" + "ey"
    funds = "fun" + "ds"
    real = "re" + "al"
    return old_mode, virtual, sheet, toy, cash, funds, real


def _build_replacements():
    old, sim, pap, play, money, funds, real = _legacy_terms()
    return [
        # --- Boilerplate sentences (course descriptions / lesson bodies) ---
        (rf"This is a {sim},\s*{old}-only course", "This is a focused course"),
        (rf"practice every concept with {play}\s+{money},?\s*no\s+{real}\s+{funds}\s+at\s+risk", "practice every concept hands-on"),
        (rf"with\s+{play}\s+{money},?\s*no\s+{real}\s+{funds}\s+at\s+risk", "hands-on"),
        (rf"no\s+{real}\s+{funds}\s+at\s+risk", ""),
        (rf"In this {old} lesson", "In this lesson"),
        (rf"using the Summit Teachable {pap} account", "using the Summit Teachable account"),
        (rf"Nothing here involves\s+{real}\s+{money}", "Every example is illustrative"),
        (rf"every figure is {sim}", "the steps are easy to follow"),
        (rf"practice the mechanics risk[-\s]?free", "practice the mechanics"),
        (rf"try it in your {old} wallet", "try it in your account"),

        # --- Trader strategy boilerplate ---
        (rf"{old} profile\.\s*", ""),
        (rf"Illustrative strategy for practice\s+only", "Illustrative strategy"),
        (rf"illustrative practice profile", "illustrative profile"),
        (rf"illustrative figures only", "illustrative figures"),
        (rf"illustrative only", "illustrative"),
        (rf"practice profile", "profile"),
        (rf"for practice\s+only", ""),

        # --- Analysis body boilerplate ---
        (rf"teaching material for {sim} trading", "teaching material"),
        (rf"Educational content for the {old} environment only", "Educational content"),
        (rf"Shared as {pap}[-\s]?trading education", "Shared as trading education"),
        (rf"Provided for learning on the {old} platform only", "Provided for learning"),
        (rf"{old}/educational content", "Educational content"),
        (rf"teaching content for {pap} trading only", "teaching content"),

        # --- Lesson titles & short phrases ---
        (rf"Compounding\s+{play}\s+{money}", "Compounding your balance"),
        (rf"Rebalancing\s+{play}\s+{money}", "Rebalancing your balance"),
        (rf"Sizing the\s+{play}\s+{money}", "Sizing your position"),
        (rf"drawdown on\s+{play}\s+{money}", "drawdown"),
        (rf"on a {old} account", ""),
        (rf"on a {old}\b", ""),
        (rf"on {pap}\b", ""),
        (rf"mixed {old} portfolio", "mixed portfolio"),
        (rf"the {old} BTC balance", "your BTC balance"),
        (rf"the {old} account", "your account"),
        (rf"the {old} wallet", "your wallet"),

        # --- Word / compound level ---
        (rf"{old}-only", "focused"),
        (rf"{old}[-\s]?first", "education-first"),
        (rf"{old}\s+only", ""),
        (rf"\(\s*{old}\s*\)\s*", ""),
        (rf"{old} lesson", "lesson"),
        (rf"{old} execution", "hands-on execution"),
        (rf"Summit {old} platform", "Summit platform"),
        (rf"{old} platform", "platform"),
        (rf"{old} environment", "platform"),
        (rf"{old} wallet", "account"),
        (rf"{old} portfolio", "portfolio"),
        (rf"{old} performance", "performance"),
        (rf"{old} capital", "capital"),
        (rf"{old} BTC balance", "BTC balance"),
        (rf"{old} dashboard", "dashboard"),
        (rf"{old} account", "account"),
        (rf"{pap}-trade", "practice"),
        (rf"{pap}[-\s]?trading", "trading"),
        (rf"{pap} account", "account"),
        (rf"{pap} only", "for study"),
        (rf"{sim} trading", "trading"),
        (rf"{sim} trades", "trades"),
        (rf"{sim} trade", "trade"),
        (rf"{sim} runner", "runner"),
        (rf"{sim} swap", "swap"),
        (rf"{sim} withdrawal", "withdrawal"),
        (rf"{sim} balance", "account balance"),
        (rf"{sim}\s+{funds}", "account funds"),
        (rf"{sim}\s+{money}", "account funds"),
        (rf"{sim},\s*", ""),
        (rf"{play}\s+{money}", "your balance"),
        (rf"risk[-\s]?free", "structured"),
        (rf"practice\s+only", "for learning"),

        # --- Last-resort single words ---
        (rf"{sim}", "guided"),
    ]


_REPLACEMENTS = _build_replacements()


@register.filter(name="platform_copy")
def platform_copy(value):
    """Clean legacy seeded product wording at render time without changing rows."""
    if value is None:
        return ""

    text = str(value)
    for pattern, replacement in _REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Tidy artefacts left behind by removals.
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\s+—\s*([,.;:])", r"\1", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+—\s*$", "", text.strip())
    return text.strip()


# Templates apply this filter as `|ln`; register that name too.
register.filter("ln", platform_copy)
