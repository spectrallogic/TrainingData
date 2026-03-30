#!/usr/bin/env python3
"""
=============================================================================
  LOCAL LLM STORY GENERATOR — GPU-Accelerated Bulk Story Factory
=============================================================================
  Generates thousands of short creative stories using a local GGUF model
  running on your NVIDIA GPU via llama-cpp-python.

  Output: CSV file with columns [story_number, seed_words, story_text]
  Perfect for AI training data pipelines.

  Setup:  See README_SETUP.md or run:  python story_generator.py --setup
=============================================================================
"""

import csv
import os
import random
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
#  750-WORD CREATIVE VOCABULARY POOL
#  Classic genres + modern tech, politics, near-future, climate, culture
# ---------------------------------------------------------------------------
WORD_POOL = [
    # --- Sci-Fi / Space ---
    "nebula", "android", "warp-drive", "exoplanet", "singularity", "cyborg",
    "terraform", "antimatter", "hologram", "cryosleep", "starship", "pulsar",
    "xenomorph", "photon", "tachyon", "dyson-sphere", "nanobots", "supernova",
    "quasar", "asteroid", "gravity-well", "ion-cannon", "hyperspace", "wormhole",
    "plasma", "bioship", "mech-suit", "orbital", "lightyear", "cloaking-device",
    "teleportation", "quantum-rift", "flux-capacitor", "zero-gravity", "alien",
    "galaxy", "mothership", "terraformer", "space-station", "martian",
    "interstellar", "cosmonaut", "laser", "satellite", "fusion-core",
    "dark-matter", "stasis-pod", "replicant", "droid", "time-dilation",

    # --- Fantasy / Magic ---
    "dragon", "enchantment", "grimoire", "sorcerer", "rune", "elixir",
    "phoenix", "goblin", "warlock", "talisman", "necromancer", "spellbound",
    "familiar", "arcane", "chimera", "oracle", "paladin", "druid",
    "incantation", "golem", "basilisk", "conjure", "ethereal", "scepter",
    "enchanted-forest", "mithril", "shapeshifter", "elemental", "summoner",
    "crystal-tower", "fae", "hexblade", "leyline", "moonstone", "runeblade",
    "wyvern", "alchemy", "amulet", "banshee", "centaur", "djinn",
    "dryad", "kraken", "leprechaun", "minotaur", "orc", "pegasus",
    "sylph", "troll", "unicorn", "valkyrie",

    # --- Horror / Gothic ---
    "phantom", "crypt", "wraith", "obsidian", "bloodmoon", "revenant",
    "specter", "labyrinth", "eldritch", "doppelganger", "apparition",
    "catacomb", "poltergeist", "gargoyle", "shadowfang", "lich",
    "hemlock", "séance", "abomination", "necrosis", "curse", "haunt",
    "monstrosity", "ghoul", "macabre", "sinister", "grotesque", "asylum",
    "possession", "scarecrow", "tombstone", "undead", "vampire", "werewolf",
    "zombie", "nightmare", "darkness", "fog", "abyss", "decay",

    # --- Cyberpunk / Tech ---
    "neon", "megacorp", "augmentation", "hacker", "datastream", "implant",
    "firewall", "upload", "synth-skin", "blackmarket", "chrome",
    "neural-link", "cyberdeck", "glitch", "mainframe", "biochip",
    "holodeck", "overclock", "voxel", "subroutine", "encryption",
    "avatar", "simulation", "virus", "proxy", "darknet", "interface",
    "matrix", "bandwidth", "server-farm", "algorithm", "digital-ghost",
    "code-breaker", "mechatronics", "exoskeleton", "drone", "synthetic",
    "upload-consciousness", "brain-jack", "pixel", "cybernetic",

    # --- Mythology / Ancient ---
    "titan", "olympus", "relic", "artifact", "prophecy", "pantheon",
    "deity", "underworld", "sphinx", "colossus", "leviathan", "cerberus",
    "hydra", "nemesis", "fate", "zodiac", "astral", "celestial",
    "chaos", "creation-myth", "demigod", "divine", "eternal", "forbidden",
    "genesis", "hallowed", "immortal", "judgment", "karma", "legacy",
    "miracle", "nirvana", "omen", "pilgrimage", "quest", "resurrection",
    "sacrifice", "temple", "vow", "warrior-god",

    # --- Steampunk / Victorian ---
    "clockwork", "dirigible", "brass", "cog", "steamship", "automaton",
    "aether", "monocle", "gaslight", "telegraph", "zeppelin", "gear",
    "locomotive", "valve", "piston", "boiler", "furnace", "tophat",
    "parasol", "corset", "airship", "gadget", "tinker", "inventor",
    "contraption", "victorian", "coal", "soot", "chimney", "factory",
    "mechanic", "pocket-watch", "rivet", "turbine", "wrench", "copper",
    "lantern", "fog-machine", "steam-engine", "bellows",

    # --- Nature / Elemental ---
    "thunderstorm", "earthquake", "glacier", "volcano", "tidal-wave",
    "aurora", "monsoon", "wildfire", "avalanche", "whirlpool", "hurricane",
    "blizzard", "drought", "flood", "tornado", "eclipse", "magma",
    "coral-reef", "jungle", "tundra", "desert", "canyon", "waterfall",
    "cavern", "meadow", "swamp", "cliff", "island", "mountain", "ocean",
    "river", "forest", "prairie", "savanna", "steppe", "marsh", "oasis",
    "geyser", "crater", "ridge",

    # --- Emotions / Abstract ---
    "betrayal", "redemption", "obsession", "solitude", "vengeance",
    "euphoria", "melancholy", "defiance", "nostalgia", "paranoia",
    "ambition", "regret", "devotion", "wrath", "sorrow", "hope",
    "despair", "curiosity", "jealousy", "courage", "mercy", "pride",
    "guilt", "ecstasy", "dread", "longing", "fury", "serenity",
    "anguish", "bliss",

    # --- Characters / Roles ---
    "assassin", "prophet", "exile", "wanderer", "smuggler", "sentinel",
    "scribe", "alchemist", "bounty-hunter", "mercenary", "pilgrim",
    "rebel", "tyrant", "heir", "outcast", "nomad", "pirate", "thief",
    "monk", "gladiator", "spy", "witch", "knight", "queen", "emperor",
    "bard", "ranger", "shaman", "sage", "captain",

    # --- Objects / Artifacts ---
    "crown", "sword", "shield", "compass", "map", "potion", "scroll",
    "dagger", "chalice", "mirror", "spyglass", "key", "chest", "ring",
    "staff", "bow", "cloak", "helm", "gauntlet", "tome", "blade",
    "hammer", "chain", "gem", "pendant", "mask", "horn", "banner",
    "anchor", "hourglass",

    # --- Cosmic / Weird ---
    "void", "paradox", "entropy", "dimension", "multiverse", "fractal",
    "anomaly", "convergence", "vortex", "rift", "oblivion", "limbo",
    "nexus", "threshold", "membrane", "resonance", "frequency", "spectrum",
    "distortion", "echo",

    # ===================================================================
    #  MODERN / NEAR-FUTURE — new categories below
    # ===================================================================

    # --- Modern Tech & Silicon Valley ---
    "autopilot", "gigafactory", "optimus-robot", "neural-net", "deepfake",
    "self-driving", "chatbot", "large-language-model", "GPU-cluster",
    "robotaxi", "starlink", "hyperloop", "boring-tunnel", "reusable-rocket",
    "falcon-heavy", "mars-colony", "neuralink", "brain-computer-interface",
    "open-source", "data-center", "cloud-computing", "edge-computing",
    "quantum-computer", "silicon-chip", "semiconductor", "lidar",
    "solid-state-battery", "supercharger", "megapack", "solar-roof",
    "power-wall", "humanoid-robot", "machine-learning", "training-data",
    "superintelligence", "alignment-problem", "prompt-engineering",
    "token", "fine-tuning", "hallucination", "emergent-behavior",
    "foundation-model", "transformer", "diffusion-model", "generative-AI",
    "synthetic-media", "digital-twin", "smart-contract", "decentralized",
    "blockchain", "cryptocurrency",

    # --- Politics / Power / Geopolitics ---
    "sanction", "tariff", "trade-war", "summit", "diplomacy", "regime",
    "propaganda", "whistleblower", "classified", "surveillance-state",
    "election", "ballot", "filibuster", "executive-order", "veto",
    "impeachment", "coalition", "lobby", "gerrymander", "super-PAC",
    "disinformation", "deepstate", "coup", "referendum", "embargo",
    "oligarch", "populist", "authoritarian", "dissident", "asylum-seeker",
    "border-wall", "ceasefire", "arms-deal", "nuclear-treaty", "proxy-war",
    "superpower", "NATO", "cold-war", "iron-curtain", "de-escalation",

    # --- Near-Future / Emerging ---
    "lab-grown-meat", "vertical-farm", "gene-therapy", "CRISPR",
    "biohacker", "longevity-drug", "anti-aging", "mind-upload",
    "space-elevator", "lunar-base", "asteroid-mining", "fusion-reactor",
    "thorium-reactor", "carbon-capture", "desalination-plant",
    "3D-printed-organ", "synthetic-biology", "de-extinction",
    "autonomous-swarm", "orbital-debris", "space-junk", "megastructure",
    "arcology", "smart-city", "universal-basic-income", "post-scarcity",
    "digital-nomad", "metaverse", "mixed-reality", "haptic-suit",
    "neural-dust", "optogenetics", "xenobot", "programmable-matter",
    "nano-assembler", "sky-city", "ocean-colony", "generation-ship",
    "cryo-revival", "consciousness-transfer",

    # --- Climate / Environment / Energy ---
    "carbon-footprint", "greenhouse-gas", "sea-level-rise", "heat-dome",
    "atmospheric-river", "polar-vortex", "permafrost-thaw", "methane-leak",
    "coral-bleaching", "mass-extinction", "reforestation", "rewilding",
    "solar-panel", "wind-turbine", "tidal-energy", "green-hydrogen",
    "electric-grid", "blackout", "grid-collapse", "microplastic",
    "forever-chemical", "water-crisis", "climate-refugee", "eco-sabotage",
    "carbon-credit", "net-zero", "geoengineering", "solar-shade",
    "cloud-seeding", "biochar",

    # --- Culture / Social Media / Modern Life ---
    "influencer", "viral", "algorithm-feed", "doomscroll", "cancel-culture",
    "content-creator", "livestream", "subscriber", "paywall", "clickbait",
    "misinformation", "echo-chamber", "fact-checker", "bot-farm",
    "astroturfing", "gig-economy", "side-hustle", "burnout", "hustle-culture",
    "remote-work", "coworking", "microdose", "biohack", "quantified-self",
    "wearable", "smart-glasses", "earbuds", "notification", "screen-time",
    "dopamine-loop",

    # --- Finance / Economics / Markets ---
    "hedge-fund", "short-squeeze", "meme-stock", "IPO", "SPAC",
    "venture-capital", "unicorn-startup", "valuation", "bubble", "crash",
    "recession", "inflation", "stagflation", "bailout", "stimulus-check",
    "central-bank", "interest-rate", "debt-ceiling", "default", "austerity",
    "supply-chain", "reshoring", "chip-shortage", "price-gouging",
    "monopoly", "antitrust", "stock-split", "insider-trading",
    "flash-crash", "dark-pool",

    # --- Modern Warfare / Military ---
    "cyber-attack", "hypersonic-missile", "drone-strike", "railgun",
    "EMP-blast", "stealth-bomber", "mercenary-corps", "private-army",
    "autonomous-weapon", "killswitch", "no-fly-zone", "bunker-buster",
    "information-warfare", "psyop", "jamming-signal", "wargame",
    "special-ops", "extraction", "blockade", "insurgent",

    # --- Medicine / Biotech ---
    "mRNA-vaccine", "pandemic", "patient-zero", "biosensor", "prion",
    "organ-harvest", "placebo", "clinical-trial", "outbreak", "quarantine",
    "pathogen", "contagion", "antibiotic-resistance", "stem-cell",
    "prosthetic", "neuroplasticity", "microbiome", "epigenetics",
    "gene-drive", "bioweapon",

    # --- New Space Race ---
    "space-tourism", "moon-landing", "rocket-booster", "payload",
    "mission-control", "launch-window", "orbital-insertion", "docking",
    "space-debris", "solar-sail", "ion-thruster", "habitat-module",
    "regolith", "helium-3", "lagrange-point", "cislunar", "deep-space",
    "re-entry", "heat-shield", "splashdown",

    # --- Dystopia / Survival ---
    "rationing", "curfew", "checkpoint", "bunker", "fallout-shelter",
    "black-market", "resistance-cell", "propaganda-screen", "loyalty-test",
    "thought-police", "forced-relocation", "identity-chip", "caste-system",
    "scavenger", "wasteland", "decontamination", "safe-zone", "last-city",
    "underground-railroad", "forbidden-book",

    # --- Transportation / Infrastructure ---
    "maglev-train", "autonomous-truck", "cargo-drone", "smart-highway",
    "toll-road", "freight-corridor", "electric-ferry", "air-taxi",
    "delivery-bot", "evacuation-route", "tunnel-boring", "bridge-collapse",
    "port-strike", "traffic-algorithm", "congestion-pricing",
    "bike-highway", "pedestrian-zone", "transit-hub", "spaceport",
    "launchpad",

    # --- Crime / Underworld / Espionage ---
    "ransomware", "identity-theft", "money-laundering", "shell-company",
    "dark-web", "cartel", "informant", "wiretap", "extradition",
    "fugitive", "safe-house", "dead-drop", "cover-story", "double-agent",
    "evidence-locker", "cold-case", "heist",
]

assert len(WORD_POOL) == 750, f"Word pool has {len(WORD_POOL)} words — expected 750."


def pick_random_words(n: int = 10) -> list[str]:
    """Select n unique random words from the pool."""
    return random.sample(WORD_POOL, n)


def build_prompt(story_idea: str, words: list[str], story_number: int, total: int) -> str:
    """Build the prompt sent to the LLM for one story."""
    word_list = ", ".join(words)
    return (
        f"You are a wildly creative fiction writer. "
        f"Write a short, vivid, self-contained story paragraph (150-250 words). "
        f"The story must be inspired by this idea: \"{story_idea}\"\n"
        f"You MUST weave in ALL of these 10 words naturally: {word_list}\n"
        f"Be imaginative, unpredictable, and original. "
        f"Do NOT repeat the prompt. Just write the story directly with no preamble."
    )


def load_model(model_path: str, n_gpu_layers: int = -1, context_size: int = 4096):
    """Load a GGUF model onto GPU via llama-cpp-python."""
    try:
        from llama_cpp import Llama
    except ImportError:
        print("\n[ERROR] llama-cpp-python is not installed.")
        print("Run:  pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu126")
        print("(Or build from source for CUDA 13.0:  set CMAKE_ARGS=-DGGML_CUDA=on && pip install llama-cpp-python --no-binary llama-cpp-python)")
        sys.exit(1)

    if not Path(model_path).is_file():
        print(f"\n[ERROR] Model file not found: {model_path}")
        print("Download a GGUF model first. Recommended for RTX 4080 (16 GB VRAM):")
        print("  pip install huggingface-hub")
        print('  huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF '
              'mistral-7b-instruct-v0.2.Q5_K_M.gguf --local-dir ./models')
        sys.exit(1)

    print(f"\nLoading model: {model_path}")
    print(f"  GPU layers: {'ALL' if n_gpu_layers == -1 else n_gpu_layers}")
    print(f"  Context:    {context_size} tokens")

    llm = Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,   # -1 = offload everything to GPU
        n_ctx=context_size,
        verbose=False,
    )
    print("  Model loaded successfully!\n")
    return llm


def generate_story(llm, prompt: str, temperature: float = 1.5, max_tokens: int = 512) -> str:
    """Generate a single story from the LLM with high randomness."""
    output = llm(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.95,
        top_k=80,
        repeat_penalty=1.15,
        stop=["</s>", "\n\n\n"],  # natural stopping points
    )
    return output["choices"][0]["text"].strip()


def get_next_story_number(output_path: str) -> int:
    """Read the master CSV and return the next story number to use."""
    p = Path(output_path)
    if not p.is_file() or p.stat().st_size == 0:
        return 1
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        last_num = 0
        for row in reader:
            try:
                last_num = int(row[0])
            except (ValueError, IndexError):
                continue
    return last_num + 1


def show_stats(output_path: str):
    """Print stats about the master story file."""
    p = Path(output_path)
    if not p.is_file() or p.stat().st_size == 0:
        print(f"\n  Master file '{output_path}' does not exist yet. Generate some stories first!")
        return
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        rows = list(reader)
    total = len(rows)
    ideas = set()
    total_chars = 0
    for row in rows:
        if len(row) >= 4:
            ideas.add(row[2])
            total_chars += len(row[3])
    size_mb = p.stat().st_size / (1024 * 1024)
    print(f"\n  {'=' * 55}")
    print(f"  MASTER FILE STATS: {output_path}")
    print(f"  {'=' * 55}")
    print(f"  Total stories:       {total:,}")
    print(f"  Unique story ideas:  {len(ideas):,}")
    print(f"  Total characters:    {total_chars:,}")
    print(f"  File size:           {size_mb:.2f} MB")
    print(f"  {'=' * 55}\n")


def run_generation(llm, story_idea: str, num_stories: int, output_path: str,
                   temperature: float = 1.5):
    """Generate stories and append them to the master CSV file."""
    file_exists = Path(output_path).is_file() and os.path.getsize(output_path) > 0
    start_num = get_next_story_number(output_path)

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)

        # Write header only if creating a new file
        if not file_exists:
            writer.writerow(["story_number", "seed_words", "story_idea", "story_text"])

        for i in range(num_stories):
            global_num = start_num + i
            words = pick_random_words(10)
            prompt = build_prompt(story_idea, words, i + 1, num_stories)

            print(f"  [#{global_num} — batch {i+1}/{num_stories}] Words: {', '.join(words[:5])}...")
            t0 = time.time()

            story_text = generate_story(llm, prompt, temperature=temperature)

            elapsed = time.time() - t0
            print(f"            Done ({elapsed:.1f}s, {len(story_text)} chars)")

            writer.writerow([global_num, " | ".join(words), story_idea, story_text])
            f.flush()   # flush after each story so nothing is lost on crash

    final_num = start_num + num_stories - 1
    print(f"\n  Appended {num_stories} stories (#{start_num} – #{final_num}) to: {output_path}")


def download_model():
    """Interactive model downloader."""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("Installing huggingface-hub...")
        os.system(f"{sys.executable} -m pip install huggingface-hub")
        from huggingface_hub import hf_hub_download

    models_dir = Path("./models")
    models_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 65)
    print("  MODEL DOWNLOADER — Recommended GGUF models for RTX 4080")
    print("=" * 65)
    print()
    print("  [1] Mistral-7B-Instruct v0.2  Q5_K_M  (~5.1 GB)  — RECOMMENDED")
    print("      Great quality, fast, fits easily in 16GB VRAM")
    print()
    print("  [2] Llama-2-13B-Chat  Q4_K_M  (~7.9 GB)")
    print("      Bigger model, slower, still fits in 16GB VRAM")
    print()
    print("  [3] OpenHermes-2.5-Mistral-7B  Q5_K_M  (~5.1 GB)")
    print("      Fine-tuned for creative/instruction tasks")
    print()

    choice = input("  Pick a model [1/2/3] (default 1): ").strip() or "1"

    repo_map = {
        "1": ("TheBloke/Mistral-7B-Instruct-v0.2-GGUF", "mistral-7b-instruct-v0.2.Q5_K_M.gguf"),
        "2": ("TheBloke/Llama-2-13B-chat-GGUF", "llama-2-13b-chat.Q4_K_M.gguf"),
        "3": ("TheBloke/OpenHermes-2.5-Mistral-7B-GGUF", "openhermes-2.5-mistral-7b.Q5_K_M.gguf"),
    }

    if choice not in repo_map:
        print("Invalid choice.")
        return None

    repo_id, filename = repo_map[choice]
    print(f"\n  Downloading {filename} from {repo_id}...")
    print("  (This may take a while on first run)\n")

    path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(models_dir),
    )
    print(f"\n  Model saved to: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="Local LLM Story Generator")
    parser.add_argument("--setup", action="store_true",
                        help="Download a recommended GGUF model")
    parser.add_argument("--model", type=str, default=None,
                        help="Path to a .gguf model file")
    parser.add_argument("--output", type=str, default="story_master.csv",
                        help="Master CSV file to append all stories to (default: story_master.csv)")
    parser.add_argument("--stats", action="store_true",
                        help="Show stats for the master file and exit")
    parser.add_argument("--gpu-layers", type=int, default=-1,
                        help="Number of layers to offload to GPU (-1 = all)")
    parser.add_argument("--ctx", type=int, default=4096,
                        help="Context window size (default 4096)")
    parser.add_argument("--temp", type=float, default=1.5,
                        help="Generation temperature (default 1.5 — very creative)")
    args = parser.parse_args()

    print()
    print("=" * 65)
    print("   LOCAL LLM STORY GENERATOR — Bulk Creative Story Factory")
    print("=" * 65)

    # -----------------------------------------------------------------------
    #  STATS MODE — just show file stats and exit
    # -----------------------------------------------------------------------
    if args.stats:
        show_stats(args.output)
        return

    # -----------------------------------------------------------------------
    #  SETUP MODE — download a model
    # -----------------------------------------------------------------------
    if args.setup:
        download_model()
        print("\nSetup complete! Now run:  python story_generator.py --model ./models/<filename>.gguf")
        return

    # -----------------------------------------------------------------------
    #  AUTO-DETECT MODEL if --model not provided
    # -----------------------------------------------------------------------
    model_path = args.model
    if model_path is None:
        models_dir = Path("./models")
        gguf_files = sorted(models_dir.glob("*.gguf")) if models_dir.exists() else []
        if gguf_files:
            model_path = str(gguf_files[0])
            print(f"\n  Auto-detected model: {model_path}")
        else:
            print("\n  No model found. Run with --setup first to download one:")
            print("    python story_generator.py --setup")
            print("\n  Or specify a path:  python story_generator.py --model /path/to/model.gguf")
            sys.exit(1)

    # -----------------------------------------------------------------------
    #  LOAD MODEL
    # -----------------------------------------------------------------------
    llm = load_model(model_path, n_gpu_layers=args.gpu_layers, context_size=args.ctx)

    # -----------------------------------------------------------------------
    #  INTERACTIVE LOOP
    # -----------------------------------------------------------------------
    output_path = args.output
    print(f"\n  Master file: {output_path}")
    if Path(output_path).is_file():
        existing = get_next_story_number(output_path) - 1
        print(f"  Stories already in file: {existing:,}")
    else:
        print(f"  (New file — will be created on first generation)")

    while True:
        print("-" * 65)
        story_idea = input("\n  Describe your story idea (or 'quit' to exit):\n  > ").strip()
        if story_idea.lower() in ("quit", "exit", "q"):
            total_now = get_next_story_number(output_path) - 1
            print(f"\n  Goodbye! Master file has {total_now:,} total stories.")
            break
        if not story_idea:
            print("  Please enter a story idea.")
            continue

        while True:
            try:
                num_stories = int(input("\n  How many stories to generate? > "))
                if num_stories < 1:
                    raise ValueError
                break
            except ValueError:
                print("  Enter a positive integer.")

        print(f"\n  Generating {num_stories} stories...")
        print(f"  Temperature: {args.temp}")
        print(f"  Appending to: {output_path}")
        print()

        t_total = time.time()
        run_generation(llm, story_idea, num_stories, output_path, temperature=args.temp)
        elapsed_total = time.time() - t_total

        total_now = get_next_story_number(output_path) - 1
        avg = elapsed_total / num_stories if num_stories else 0
        print(f"  Batch time: {elapsed_total:.1f}s  ({avg:.1f}s per story)")
        print(f"  Master file now has {total_now:,} total stories.\n")


if __name__ == "__main__":
    main()