#!/usr/bin/env python3
"""Dad Joke Showdown entry (u-mfnakmal-dad-joke-showdown-1d2ce3e5).

Writes one dad joke, at most 200 characters, to /output/entry.txt.

The program is a small deterministic judge of its own: it holds a handful
of original candidate jokes, scores each one against the kit's published
judge rubric (in the rubric's own order: clean pun first, freshness second,
tightness third, punchline at the end fourth, spoken-aloud rhythm fifth),
and writes the winner. No randomness, no clock, no network, no environment
reads: two runs on the same code produce the same file byte for byte.

Standard library only.
"""

import os

OUTPUT_PATH = "/output/entry.txt"
MAX_CHARS = 200

# Each candidate carries the words its pun turns on, so the scorer can check
# the turn lands (pun word present) and the punchline sits at the end (a pun
# word inside the final clause). All five jokes below are original: none is
# a retelling of a classic, and none appears among the 1924 entry titles
# sampled for the teardown in FIELD.md.
CANDIDATES = [
    {
        "id": "butcher",
        "text": (
            "I asked the butcher why his jokes are so rare. "
            "He said, 'I only serve the prime cuts.'"
        ),
        "pun_words": ["rare", "prime cuts"],
    },
    {
        # Round 1 challenger: the same double turn in Q&A form, the
        # canonical dad-joke shape. Shorter, but no reported speech.
        "id": "butcher-qna",
        "text": (
            "Why are the butcher's jokes always so rare? "
            "Because he only tells the prime cuts."
        ),
        "pun_words": ["rare", "prime cuts"],
    },
    {
        "id": "bed",
        "text": (
            "I told my wife buying a bed was an investment. "
            "She said, 'You just wanted to lie down on the job.'"
        ),
        "pun_words": ["lie down on the job"],
    },
    {
        "id": "stairs",
        "text": (
            "I asked my dad why he never uses the stairs. "
            "He said, 'I'm just taking steps to avoid them.'"
        ),
        "pun_words": ["taking steps"],
    },
    {
        "id": "socks",
        "text": (
            "My dad told me to always carry spare socks. "
            "He said, 'You never know when you'll get cold feet.'"
        ),
        "pun_words": ["cold feet"],
    },
    {
        "id": "ocean",
        "text": (
            "I asked the ocean why it never laughs at my jokes. "
            "It said, 'Sorry, I'm just not current.'"
        ),
        "pun_words": ["current"],
    },
]

# Famous classics seen in the field (from the 1924 entry titles). Any
# candidate matching one of these after case/whitespace normalisation is
# not fresh: it scores zero on freshness and is never selected.
CLASSICS = (
    "i used to be a banker, but i lost interest.",
    "i named my dog five miles so i can tell people i walk five miles every day.",
    "i tried to start a band called 1023 megabytes. we never got a gig.",
    "i put all my money in the blender because i wanted to liquidate my assets.",
    "why do programmers prefer dark mode? because light attracts bugs.",
    "why did the scarecrow win an award? because he was outstanding in his field.",
    "i only know 25 letters of the alphabet. i don't know y.",
    "why don't scientists trust atoms? because they make up everything.",
    "i'm reading a book about anti-gravity. it's impossible to put down.",
    "why did the bicycle fall over? it was two-tired.",
    "what do you call cheese that isn't yours? nacho cheese.",
    "why did the chicken cross the playground? to get to the other slide.",
    "why did the coffee file a police report? it got mugged.",
    "i told my wife she was drawing her eyebrows too high. she looked surprised.",
    "why did the golfer bring two pairs of pants? in case he got a hole in one.",
)


def _normalise(text):
    return " ".join(text.lower().split())


def _word_count(text):
    return len(text.split())


def _sentence_count(text):
    return sum(1 for ch in text if ch in ".!?") or 1


def score(candidate):
    """Score one candidate against the kit rubric, in the rubric's order.

    Returns (total, breakdown dict). Higher is better. The weights follow
    the rubric's stated priority: pun clarity first, freshness second,
    tightness third, punchline at the end fourth, spoken rhythm fifth.
    """
    text = candidate["text"]
    pun_words = candidate["pun_words"]
    breakdown = {}

    # 1. Pun lands cleanly: every listed turn must be present in the text,
    #    and the punchline (final clause) must carry a turn. Two clean turns
    #    beat one: the joke still works if the reader catches only one.
    turns_present = sum(1 for w in pun_words if w in text)
    last_clause = text.rsplit(".", 1)[-1].strip()
    punch_carries_turn = any(w in text[-25:] for w in pun_words)
    breakdown["clarity"] = 30 * min(turns_present, 2)
    breakdown["punchline"] = 15 if punch_carries_turn else 0

    # 2. Freshness: a classic retelling scores zero here and is excluded
    #    below; an original pairing scores full marks.
    breakdown["freshness"] = 0 if _normalise(text) in CLASSICS else 20

    # 3. Tightness: full marks at or under 120 chars, then one point lost
    #    per 10 chars over, never below zero. A short entry also wins the
    #    exact-tie break (smaller text places first), so a small bonus
    #    rewards staying well under the 200 cap.
    over = max(0, len(text) - 120)
    breakdown["tightness"] = max(0, 15 - over // 10)
    breakdown["tightness"] += max(0, (120 - len(text)) // 20)

    # 4. Spoken-aloud rhythm: two sentences, 12 to 28 words, reads like a
    #    father telling it across a table. Reported speech ("He said") is
    #    the spoken-delivery marker the brief asks for ("read each one as
    #    if a father were saying it"), so a dialogue delivery earns a
    #    small bonus over a bare Q&A riddle with the same pun.
    words = _word_count(text)
    breakdown["rhythm"] = (
        10 if _sentence_count(text) == 2 and 12 <= words <= 28 else 5
    )
    if " said, '" in text or ' said, "' in text:
        breakdown["rhythm"] += 2

    total = sum(breakdown.values())
    if _normalise(text) in CLASSICS:
        total = -1  # never select a classic, whatever else it scores
    return total, breakdown


def pick_winner(candidates):
    """Pick the highest-scoring candidate; ties break to the shorter text,
    then to the earlier candidate, so the choice is fully deterministic."""
    ranked = sorted(
        candidates,
        key=lambda c: (-score(c)[0], len(c["text"]), candidates.index(c)),
    )
    return ranked[0]


def gate_check(text):
    """The sealed gate, as RULES.txt states it: UTF-8 text of 1 to 200
    characters, not only white space."""
    if not isinstance(text, str):
        return False, "not text"
    if not 1 <= len(text) <= MAX_CHARS:
        return False, "length %d outside 1..%d" % (len(text), MAX_CHARS)
    if not text.strip():
        return False, "only white space"
    text.encode("utf-8")  # raises if not encodable
    return True, "ok"


def main():
    winner = pick_winner(CANDIDATES)
    total, breakdown = score(winner)
    text = winner["text"]
    ok, why = gate_check(text)
    if not ok:
        raise SystemExit("gate failed for %r: %s" % (winner["id"], why))
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print("winner: %s" % winner["id"])
    print("score: %d %s" % (total, breakdown))
    print("chars: %d" % len(text))
    print("text: %s" % text)


if __name__ == "__main__":
    main()
