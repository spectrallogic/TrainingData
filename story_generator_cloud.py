#!/usr/bin/env python3
"""
Groq Cloud Story Generator

Generates short creative stories in batches using the Groq API and appends
results to a CSV file. Reads GROQ_API_KEY from a .env file.

Install:
    pip install groq python-dotenv

Examples:
    python story_generator_cloud.py --idea "A city that wakes up underwater" --count 50
    python story_generator_cloud.py --idea "A city that wakes up underwater" --count 50 --include-seed-words
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import time
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: groq\nInstall with: pip install groq python-dotenv"
    ) from exc


DEFAULT_MODEL = "llama-3.1-8b-instant"
DEFAULT_OUTPUT = "story_master.csv"
DEFAULT_BATCH_SIZE = 8
DEFAULT_MIN_WORDS = 900
DEFAULT_MAX_WORDS = 1100

# Same creative word pool concept from the local generator. Adapted so the
# cloud version keeps the same random-creativity stimulation behavior.
WORD_POOL = [
    "nebula", "android", "warp-drive", "exoplanet", "singularity", "cyborg",
    "terraform", "antimatter", "hologram", "cryosleep", "starship", "pulsar",
    "xenomorph", "photon", "tachyon", "dyson-sphere", "nanobots", "supernova",
    "quasar", "asteroid", "gravity-well", "ion-cannon", "hyperspace", "wormhole",
    "plasma", "bioship", "mech-suit", "orbital", "lightyear", "cloaking-device",
    "teleportation", "quantum-rift", "flux-capacitor", "zero-gravity", "alien",
    "galaxy", "mothership", "terraformer", "space-station", "martian",
    "interstellar", "cosmonaut", "laser", "satellite", "fusion-core",
    "dark-matter", "stasis-pod", "replicant", "droid", "time-dilation",
    "dragon", "enchantment", "grimoire", "sorcerer", "rune", "elixir",
    "phoenix", "goblin", "warlock", "talisman", "necromancer", "spellbound",
    "familiar", "arcane", "chimera", "oracle", "paladin", "druid",
    "incantation", "golem", "basilisk", "conjure", "ethereal", "scepter",
    "enchanted-forest", "mithril", "shapeshifter", "elemental", "summoner",
    "crystal-tower", "fae", "hexblade", "leyline", "moonstone", "runeblade",
    "wyvern", "alchemy", "amulet", "banshee", "centaur", "djinn",
    "dryad", "kraken", "leprechaun", "minotaur", "orc", "pegasus",
    "sylph", "troll", "unicorn", "valkyrie", "phantom", "crypt",
    "wraith", "obsidian", "bloodmoon", "revenant", "specter", "labyrinth",
    "eldritch", "doppelganger", "apparition", "catacomb", "poltergeist", "gargoyle",
    "shadowfang", "lich", "hemlock", "séance", "abomination", "necrosis",
    "curse", "haunt", "monstrosity", "ghoul", "macabre", "sinister",
    "grotesque", "asylum", "possession", "scarecrow", "tombstone", "undead",
    "vampire", "werewolf", "zombie", "nightmare", "darkness", "fog",
    "abyss", "decay", "neon", "megacorp", "augmentation", "hacker",
    "datastream", "implant", "firewall", "upload", "synth-skin", "blackmarket",
    "chrome", "neural-link", "cyberdeck", "glitch", "mainframe", "biochip",
    "holodeck", "overclock", "voxel", "subroutine", "encryption", "avatar",
    "simulation", "virus", "proxy", "darknet", "interface", "matrix",
    "bandwidth", "server-farm", "algorithm", "digital-ghost", "code-breaker", "mechatronics",
    "exoskeleton", "drone", "synthetic", "upload-consciousness", "brain-jack", "pixel",
    "cybernetic", "titan", "olympus", "relic", "artifact", "prophecy",
    "pantheon", "deity", "underworld", "sphinx", "colossus", "leviathan",
    "cerberus", "hydra", "nemesis", "fate", "zodiac", "astral",
    "celestial", "chaos", "creation-myth", "demigod", "divine", "eternal",
    "forbidden", "genesis", "hallowed", "immortal", "judgment", "karma",
    "legacy", "miracle", "nirvana", "omen", "pilgrimage", "quest",
    "resurrection", "sacrifice", "temple", "vow", "warrior-god", "clockwork",
    "dirigible", "brass", "cog", "steamship", "automaton", "aether",
    "monocle", "gaslight", "telegraph", "zeppelin", "gear", "locomotive",
    "valve", "piston", "boiler", "furnace", "tophat", "parasol",
    "corset", "airship", "gadget", "tinker", "inventor", "contraption",
    "victorian", "coal", "soot", "chimney", "factory", "mechanic",
    "pocket-watch", "rivet", "turbine", "wrench", "copper", "lantern",
    "fog-machine", "steam-engine", "bellows", "thunderstorm", "earthquake", "glacier",
    "volcano", "tidal-wave", "aurora", "monsoon", "wildfire", "avalanche",
    "whirlpool", "hurricane", "blizzard", "drought", "flood", "tornado",
    "eclipse", "magma", "coral-reef", "jungle", "tundra", "desert",
    "canyon", "waterfall", "cavern", "meadow", "swamp", "cliff",
    "island", "mountain", "ocean", "river", "forest", "prairie",
    "savanna", "steppe", "marsh", "oasis", "geyser", "crater",
    "ridge", "betrayal", "redemption", "obsession", "solitude", "vengeance",
    "euphoria", "melancholy", "defiance", "nostalgia", "paranoia", "ambition",
    "regret", "devotion", "wrath", "sorrow", "hope", "despair",
    "curiosity", "jealousy", "courage", "mercy", "pride", "guilt",
    "ecstasy", "dread", "longing", "fury", "serenity", "anguish",
    "bliss", "assassin", "prophet", "exile", "wanderer", "smuggler",
    "sentinel", "scribe", "alchemist", "bounty-hunter", "mercenary", "pilgrim",
    "rebel", "tyrant", "heir", "outcast", "nomad", "pirate",
    "thief", "monk", "gladiator", "spy", "witch", "knight",
    "queen", "emperor", "bard", "ranger", "shaman", "sage",
    "captain", "crown", "sword", "shield", "compass", "map",
    "potion", "scroll", "dagger", "chalice", "mirror", "spyglass",
    "key", "chest", "ring", "staff", "bow", "cloak",
    "helm", "gauntlet", "tome", "blade", "hammer", "chain",
    "gem", "pendant", "mask", "horn", "banner", "anchor",
    "hourglass", "void", "paradox", "entropy", "dimension", "multiverse",
    "fractal", "anomaly", "convergence", "vortex", "rift", "oblivion",
    "limbo", "nexus", "threshold", "membrane", "resonance", "frequency",
    "spectrum", "distortion", "echo", "autopilot", "gigafactory", "optimus-robot",
    "neural-net", "deepfake", "self-driving", "chatbot", "large-language-model", "GPU-cluster",
    "robotaxi", "starlink", "hyperloop", "boring-tunnel", "reusable-rocket", "falcon-heavy",
    "mars-colony", "neuralink", "brain-computer-interface", "open-source", "data-center",
    "cloud-computing", "edge-computing", "quantum-computer", "silicon-chip", "semiconductor",
    "lidar", "solid-state-battery", "supercharger", "megapack", "solar-roof",
    "power-wall", "humanoid-robot", "machine-learning", "training-data", "superintelligence",
    "alignment-problem", "prompt-engineering", "token", "fine-tuning", "hallucination",
    "emergent-behavior", "foundation-model", "transformer", "diffusion-model", "generative-AI",
    "synthetic-media", "digital-twin", "smart-contract", "decentralized", "blockchain",
    "cryptocurrency", "sanction", "tariff", "trade-war", "summit", "diplomacy",
    "regime", "propaganda", "whistleblower", "classified", "surveillance-state",
    "election", "ballot", "filibuster", "executive-order", "veto", "impeachment",
    "coalition", "lobby", "gerrymander", "super-PAC", "disinformation", "deepstate",
    "coup", "referendum", "embargo", "oligarch", "populist", "authoritarian",
    "dissident", "asylum-seeker", "border-wall", "ceasefire", "arms-deal", "nuclear-treaty",
    "proxy-war", "superpower", "NATO", "cold-war", "iron-curtain", "de-escalation",
    "lab-grown-meat", "vertical-farm", "gene-therapy", "CRISPR", "biohacker", "longevity-drug",
    "anti-aging", "mind-upload", "space-elevator", "lunar-base", "asteroid-mining", "fusion-reactor",
    "thorium-reactor", "carbon-capture", "desalination-plant", "3D-printed-organ", "synthetic-biology",
    "de-extinction", "autonomous-swarm", "orbital-debris", "space-junk", "megastructure",
    "arcology", "smart-city", "universal-basic-income", "post-scarcity", "digital-nomad",
    "metaverse", "mixed-reality", "haptic-suit", "neural-dust", "optogenetics", "xenobot",
    "programmable-matter", "nano-assembler", "sky-city", "ocean-colony", "generation-ship",
    "cryo-revival", "consciousness-transfer", "carbon-footprint", "greenhouse-gas", "sea-level-rise",
    "heat-dome", "atmospheric-river", "polar-vortex", "permafrost-thaw", "methane-leak",
    "coral-bleaching", "mass-extinction", "reforestation", "rewilding", "solar-panel",
    "wind-turbine", "tidal-energy", "green-hydrogen", "electric-grid", "blackout",
    "grid-collapse", "microplastic", "forever-chemical", "water-crisis", "climate-refugee",
    "eco-sabotage", "carbon-credit", "net-zero", "geoengineering", "solar-shade",
    "cloud-seeding", "biochar", "influencer", "viral", "algorithm-feed", "doomscroll",
    "cancel-culture", "content-creator", "livestream", "subscriber", "paywall", "clickbait",
    "misinformation", "echo-chamber", "fact-checker", "bot-farm", "astroturfing", "gig-economy",
    "side-hustle", "burnout", "hustle-culture", "remote-work", "coworking", "microdose",
    "biohack", "quantified-self", "wearable", "smart-glasses", "earbuds", "notification",
    "screen-time", "dopamine-loop", "hedge-fund", "short-squeeze", "meme-stock", "IPO",
    "SPAC", "venture-capital", "unicorn-startup", "valuation", "bubble", "crash",
    "recession", "inflation", "stagflation", "bailout", "stimulus-check", "central-bank",
    "interest-rate", "debt-ceiling", "default", "austerity", "supply-chain", "reshoring",
    "chip-shortage", "price-gouging", "monopoly", "antitrust", "stock-split", "insider-trading",
    "flash-crash", "dark-pool", "cyber-attack", "hypersonic-missile", "drone-strike", "railgun",
    "EMP-blast", "stealth-bomber", "mercenary-corps", "private-army", "autonomous-weapon", "killswitch",
    "no-fly-zone", "bunker-buster", "information-warfare", "psyop", "jamming-signal", "wargame",
    "special-ops", "extraction", "blockade", "insurgent", "mRNA-vaccine", "pandemic",
    "patient-zero", "biosensor", "prion", "organ-harvest", "placebo", "clinical-trial",
    "outbreak", "quarantine", "pathogen", "contagion", "antibiotic-resistance", "stem-cell",
    "prosthetic", "neuroplasticity", "microbiome", "epigenetics", "gene-drive", "bioweapon",
    "space-tourism", "moon-landing", "rocket-booster", "payload", "mission-control", "launch-window",
    "orbital-insertion", "docking", "space-debris", "solar-sail", "ion-thruster", "habitat-module",
    "regolith", "helium-3", "lagrange-point", "cislunar", "deep-space", "re-entry",
    "heat-shield", "splashdown", "rationing", "curfew", "checkpoint", "bunker",
    "fallout-shelter", "black-market", "resistance-cell", "propaganda-screen", "loyalty-test",
    "thought-police", "forced-relocation", "identity-chip", "caste-system", "scavenger", "wasteland",
    "decontamination", "safe-zone", "last-city", "underground-railroad", "forbidden-book",
    "maglev-train", "autonomous-truck", "cargo-drone", "smart-highway", "toll-road", "freight-corridor",
    "electric-ferry", "air-taxi", "delivery-bot", "evacuation-route", "tunnel-boring", "bridge-collapse",
    "port-strike", "traffic-algorithm", "congestion-pricing", "bike-highway", "pedestrian-zone", "transit-hub",
    "spaceport", "launchpad", "ransomware", "identity-theft", "money-laundering", "shell-company",
    "dark-web", "cartel", "informant", "wiretap", "extradition", "fugitive",
    "safe-house", "dead-drop", "cover-story", "double-agent", "evidence-locker", "cold-case", "heist",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate creative stories with the Groq API.")
    parser.add_argument("--idea", type=str, required=True, help="Your story idea or prompt.")
    parser.add_argument("--count", type=int, default=100, help="Number of stories to generate.")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT, help="CSV file to append to.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Groq model ID.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Stories per API call.")
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument("--temperature", type=float, default=1.25)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--sleep-between-batches", type=float, default=0.2)
    parser.add_argument("--target-total-words", type=int, default=0, help="Keep generating until total CSV words reach this value.")
    parser.add_argument("--preview", action="store_true", help="Print a sample while running.")
    parser.add_argument("--seed-words-per-story", type=int, default=10, help="Random creativity words per story.")
    parser.add_argument("--include-seed-words", action="store_true", help="Add a seed_words column like the local generator style.")
    return parser.parse_args()


def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "Missing GROQ_API_KEY. Put it in a .env file like:\n\n"
            "GROQ_API_KEY=your_key_here\n"
        )
    return api_key


def get_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


def pick_random_words(n: int = 10) -> list[str]:
    if n < 1:
        raise ValueError("seed word count must be at least 1")
    if n > len(WORD_POOL):
        raise ValueError("seed word count cannot exceed the word pool size")
    return random.sample(WORD_POOL, n)


def ensure_csv(output_path: str, include_seed_words: bool) -> None:
    path = Path(output_path)
    if not path.exists() or path.stat().st_size == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            if include_seed_words:
                writer.writerow(["story_number", "seed_words", "story_text"])
            else:
                writer.writerow(["story_number", "story_text"])


def detect_csv_mode(output_path: str, include_seed_words: bool) -> bool:
    path = Path(output_path)
    if not path.exists() or path.stat().st_size == 0:
        return include_seed_words
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
    return len(header) >= 3 and header[1].strip().lower() == "seed_words"


def get_next_story_number(output_path: str) -> int:
    path = Path(output_path)
    if not path.exists() or path.stat().st_size == 0:
        return 1
    last_num = 0
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if not row:
                continue
            try:
                last_num = int(row[0])
            except (ValueError, IndexError):
                continue
    return last_num + 1


def csv_total_word_count(output_path: str) -> int:
    path = Path(output_path)
    if not path.exists() or path.stat().st_size == 0:
        return 0
    total = 0
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 3:
                total += len(row[2].split())
            elif len(row) >= 2:
                total += len(row[1].split())
    return total


def chunked(seq: list[int], size: int) -> Iterable[list[int]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def escape_for_prompt(text: str) -> str:
    return text.replace("\r", " ").strip()


def make_seed_map(story_numbers: list[int], seed_words_per_story: int) -> dict[int, list[str]]:
    return {n: pick_random_words(seed_words_per_story) for n in story_numbers}


def build_messages(
    idea: str,
    story_numbers: list[int],
    seed_map: dict[int, list[str]],
    min_words: int,
    max_words: int,
) -> list[dict[str, str]]:
    lines = []
    for n in story_numbers:
        word_list = ", ".join(seed_map[n])
        lines.append(f"{n}: {word_list}")

    system = (
        "You are a wildly creative fiction writer generating dataset stories. "
        "Follow the user's prompt closely. Do not inject your own recurring moral themes unless the prompt asks for them. "
        "Return only valid CSV rows with exactly two columns: story_number, story_text. "
        "Do not include a header. Do not use markdown fences."
    )
    user = f"""
Story idea / prompt:
{escape_for_prompt(idea)}

Generate exactly {len(story_numbers)} CSV rows.
For each story number below, write one vivid, self-contained story inspired by the prompt.
Each story must naturally weave in ALL of its assigned seed words.

Story numbers and seed words:
{chr(10).join(lines)}

Rules:
- Each story must be between {min_words} and {max_words} words. Aim for roughly 1000 words when using the defaults.
- Be imaginative, unpredictable, and original.
- Vary settings, plot motion, sentence rhythm, and openings.
- Do not repeat the prompt.
- No bullet points.
- Keep each story as plain prose.
- Output must be parseable CSV.
""".strip()
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def request_batch(
    client: Groq,
    model: str,
    idea: str,
    story_numbers: list[int],
    seed_map: dict[int, list[str]],
    min_words: int,
    max_words: int,
    temperature: float,
    top_p: float,
    max_retries: int,
) -> str:
    messages = build_messages(idea, story_numbers, seed_map, min_words, max_words)
    delay = 1.0
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # pragma: no cover
            last_error = exc
            if attempt == max_retries:
                break
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Groq request failed after {max_retries} attempts: {last_error}")


def parse_rows(raw_csv: str) -> list[list[str]]:
    cleaned = raw_csv.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").removesuffix("```").strip()
        if cleaned.lower().startswith("csv"):
            cleaned = cleaned[3:].lstrip()

    rows: list[list[str]] = []
    reader = csv.reader(cleaned.splitlines())
    for row in reader:
        if not row:
            continue
        if row[0].strip().lower() == "story_number":
            continue
        if len(row) < 2:
            continue
        story_number = row[0].strip()
        story_text = ",".join(row[1:]).strip()
        if not story_number.isdigit() or not story_text:
            continue
        rows.append([story_number, story_text])
    return rows


def append_rows(output_path: str, rows: list[list[str]], seed_map: dict[int, list[str]], include_seed_words: bool) -> int:
    if not rows:
        return 0
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        if include_seed_words:
            out_rows = []
            for row in rows:
                seed_words = ", ".join(seed_map[int(row[0])])
                out_rows.append([row[0], seed_words, row[1]])
            writer.writerows(out_rows)
        else:
            writer.writerows(rows)
    return len(rows)


def generate_stories(args: argparse.Namespace) -> None:
    api_key = load_api_key()
    client = get_client(api_key)

    ensure_csv(args.output, args.include_seed_words)
    include_seed_words = detect_csv_mode(args.output, args.include_seed_words)
    generated = 0
    requested = max(0, args.count)
    start_number = get_next_story_number(args.output)

    while True:
        current_total_words = csv_total_word_count(args.output)
        if args.target_total_words and current_total_words >= args.target_total_words:
            print(f"Reached target total words: {current_total_words:,}")
            break
        if not args.target_total_words and generated >= requested:
            break

        remaining_by_count = requested - generated if not args.target_total_words else args.batch_size
        batch_count = min(args.batch_size, max(1, remaining_by_count))
        numbers = list(range(start_number, start_number + batch_count))
        seed_map = make_seed_map(numbers, args.seed_words_per_story)

        print(f"Generating stories {numbers[0]}-{numbers[-1]} with {args.model}...")
        raw = request_batch(
            client=client,
            model=args.model,
            idea=args.idea,
            story_numbers=numbers,
            seed_map=seed_map,
            min_words=args.min_words,
            max_words=args.max_words,
            temperature=args.temperature,
            top_p=args.top_p,
            max_retries=args.max_retries,
        )
        rows = parse_rows(raw)

        expected = {str(n) for n in numbers}
        seen: set[str] = set()
        filtered_rows: list[list[str]] = []
        for row in rows:
            if row[0] in expected and row[0] not in seen:
                filtered_rows.append(row)
                seen.add(row[0])

        missing = sorted(expected - seen, key=int)
        if missing:
            print(f"Recovered {len(filtered_rows)}/{len(numbers)} rows; retrying missing story numbers: {', '.join(missing)}")
            missing_numbers = [int(x) for x in missing]
            retry_seed_map = {n: seed_map[n] for n in missing_numbers}
            retry_raw = request_batch(
                client=client,
                model=args.model,
                idea=args.idea,
                story_numbers=missing_numbers,
                seed_map=retry_seed_map,
                min_words=args.min_words,
                max_words=args.max_words,
                temperature=args.temperature,
                top_p=args.top_p,
                max_retries=args.max_retries,
            )
            retry_rows = parse_rows(retry_raw)
            retry_seen = {r[0] for r in filtered_rows}
            for row in retry_rows:
                if row[0] in expected and row[0] not in retry_seen:
                    filtered_rows.append(row)
                    retry_seen.add(row[0])

        filtered_rows.sort(key=lambda r: int(r[0]))
        appended = append_rows(args.output, filtered_rows, seed_map, include_seed_words)
        generated += appended
        start_number += batch_count

        batch_words = sum(len(r[1].split()) for r in filtered_rows)
        print(f"Appended {appended} stories, about {batch_words:,} words. Total new stories this run: {generated:,}")

        if args.preview:
            for row in filtered_rows[:2]:
                seed_preview = ", ".join(seed_map[int(row[0])][:5])
                print(f"\n[{row[0]}] seeds: {seed_preview} ...\n{row[1][:500]}\n")

        time.sleep(max(0.0, args.sleep_between_batches))

    final_words = csv_total_word_count(args.output)
    final_next = get_next_story_number(args.output) - 1
    print("\nDone.")
    print(f"Output file: {args.output}")
    print(f"Total stories in CSV: {final_next:,}")
    print(f"Approx total words in CSV: {final_words:,}")
    print(f"Seed words column enabled: {include_seed_words}")


def main() -> None:
    args = parse_args()
    if args.count < 0:
        raise SystemExit("--count must be 0 or greater")
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1")
    if args.min_words < 1 or args.max_words < args.min_words:
        raise SystemExit("Word limits are invalid")
    if args.seed_words_per_story < 1:
        raise SystemExit("--seed-words-per-story must be at least 1")
    generate_stories(args)


if __name__ == "__main__":
    main()
