# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

---

## Run the App

```bash
python app.py
```

Open the URL shown in your terminal (usually `http://localhost:7860`).

---

## Tool Inventory

### `search_listings(description: str, size: str | None, max_price: float | None) → list[dict]`
**Purpose:** Find secondhand listings that match what the user is looking for.
**Inputs:** `description` (str) — keywords to search; `size` (str or None) — clothing size filter; `max_price` (float or None) — price ceiling.
**Output:** A list of listing dicts, each containing `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`. Sorted by relevance (most keyword matches first). Returns `[]` if nothing matches — never raises an exception.

### `suggest_outfit(new_item: dict, wardrobe: dict) → str`
**Purpose:** Help the user visualize how to wear the found item with what they already own.
**Inputs:** `new_item` (dict) — a listing dict from `search_listings`; `wardrobe` (dict) — a wardrobe object with an `items` key containing a list of wardrobe item dicts.
**Output:** A non-empty string with 1–2 outfit suggestions. If the wardrobe is empty, returns general styling advice instead of personalized combinations.

### `create_fit_card(outfit: str, new_item: dict) → str`
**Purpose:** Generate a shareable caption the user could post with their outfit photo.
**Inputs:** `outfit` (str) — the outfit suggestion string from `suggest_outfit`; `new_item` (dict) — the listing dict for the thrifted item.
**Output:** A 2–4 sentence casual, Instagram-style caption mentioning the item name, price, and platform. Uses temperature 1.2 so outputs vary each run. Returns an error string if `outfit` is empty.

---

## How the Planning Loop Works

The agent parses the user's query with regex to extract a description, size, and max price. Then it runs this conditional sequence:

1. Call `search_listings()` → if no results, set error and **stop**
2. Pick `results[0]` as the selected item
3. Call `suggest_outfit()` → if LLM fails and returns empty, set error and **stop**
4. Call `create_fit_card()` → if it returns the error string, set error and **stop**
5. Return session with all three results populated

The agent never calls `suggest_outfit` or `create_fit_card` if `search_listings` returns nothing — it branches based on what each tool returns, not a fixed sequence.

**NOTE**: This is not necessary a 'loop', it is a deterministic conditional loop, where there is an exact sequence of conditions to go through (runs once per query). This is not an agentic loop where the LLM itself decides which tools to call by returning the tool calls and loops up to K times until the LLM return the output. 

---

## State Management

A `session` dict is created at the start of each interaction and passed through the entire loop. Each tool writes its result into the session, and the next tool reads from it — the user never re-enters anything.

| Key | Set by | Used by |
|---|---|---|
| `session["selected_item"]` | Step 2 (top search result) | `suggest_outfit`, `create_fit_card` |
| `session["outfit_suggestion"]` | `suggest_outfit` | `create_fit_card` |
| `session["fit_card"]` | `create_fit_card` | UI output panel |
| `session["error"]` | Any failed step | UI (shown in first panel) |

---

## Error Handling

| Tool | Failure | What the agent does |
|---|---|---|
| `search_listings` | No results match | Sets `session["error"]` = "No listings found. Try a broader description, a higher price, or remove the size filter." Stops immediately. |
| `suggest_outfit` | Empty wardrobe | Still calls LLM with a prompt for general styling advice. Returns useful string — does not stop. |
| `suggest_outfit` | LLM returns empty | Sets `session["error"]` = "Could not generate an outfit suggestion." Stops. |
| `create_fit_card` | `outfit` is empty string | Returns "Cannot generate a fit card without an outfit suggestion." without calling LLM. |

**Concrete examples from testing:**

1. `search_listings("designer ballgown", size="XXS", max_price=5)` returns `[]` instantly. The agent sets the error message and stops — `session["fit_card"]` stays `None` and the LLM is never called.

2. `suggest_outfit(results[0], get_empty_wardrobe())` still returns useful advice despite the empty wardrobe: *"The Y2K Baby Tee pairs well with high-waisted jeans, flowy skirts, or distressed shorts for a laid-back, nostalgic look. Layer it under a cardigan or denim jacket for a casual everyday outfit."* — no crash, no empty string.

3. `create_fit_card('', results[0])` returns `"Cannot generate a fit card without an outfit suggestion."` — the guard catches the empty input and skips the LLM call entirely.

---

## Spec Reflection

**One way planning.md helped:** Writing the conditional planning loop in plain English before coding made the branching logic in `run_agent()` straightforward to implement — each numbered step in the doc mapped directly to a code block.

**One way implementation differed:** The planning.md described query parsing vaguely as "extract description, size, and max_price." In practice, this required regex patterns (`re.search`, `re.sub`) to reliably pull structured values out of free-form text — something the spec didn't anticipate in detail.

---

## AI Usage

**Instance 1 — Tool implementations (Milestone 3):**
I gave Claude the Tool 1 spec block from `planning.md` (inputs, return value, failure mode) and the `TODO` steps from `tools.py`, and asked it to implement `search_listings()` using `load_listings()` from the data loader. I reviewed the generated code to confirm it filtered by all three parameters and handled the empty-results case, then ran pytest before using it. The same process was repeated for Tools 2 and 3 one at a time.

**Instance 2 — Planning loop (Milestone 4):**
I gave Claude the Planning Loop section and Architecture diagram from `planning.md` and asked it to implement `run_agent()` in `agent.py`. I verified the generated code branched on the `search_listings` result (not calling all tools unconditionally), stored values in the `session` dict correctly, and passed state between tools without re-prompting the user.

**Instance 3 — Clarifying planning.md and README:**
I asked Claude to review my `planning.md` and `README.md` to identify gaps, correct misunderstandings (such as whether `suggest_outfit` should stop on an empty wardrobe), and improve sentence clarity for the reader.