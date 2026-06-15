# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Searches the listings dataset and returns items that match the user's description, size, and price limit. Return an empty list if nothing matches

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): keywords describing the item the user wants.
- `size` (str): the user's clothing size (None to skip size filtering).
- `max_price` (float): the highest price the user is willing to pay.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of listing dicts. Each dict has: id, title, description, category, style_tags, size, condition, price, colors, brand, platform.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
Returns [] if no matches found. The agent sets session["error"] to "No listings found. Try a broader description, a higher price, or remove the size filter." and stops — does not call suggest_outfit or create_fit_card.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a found listing and the user's wardrobe, uses the LLM to suggest one complete outfit combination using the new item.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): the selected listing dict from `search_listing`.
- `wardrobe` (dict): a wardrobe object with an `items` key containing a list of wardrobe item dicts.

**What it returns:**
<!-- Describe the return value -->
A string, a brief outfit suggestion.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If wardrobe['items'] is empty, still call the LLM but prompt it to give general styling advice for the item without referencing a specific wardrobe.
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Uses the LLM to generate a short caption for the outfit.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): the outfit suggestion string from suggest_outfit.
- `new_item` (dict): the selected listing dict.

**What it returns:**
<!-- Describe the return value -->
A string, a 1-2 sentence caption.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If `outfit` is an empty string, return "Cannot generate a fit card without an outfit suggestion." Do not call the LLM.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
1. Call `search_listings(description, size, max_price)`.
2. If `results == []`: set `session["error"]` = "No listings found. Try a broader description, a higher price, or remove the size filter." Return session. Stop here — do not call the remaining tools.
3. If `results` is not empty: set `session["selected_item"] = results[0]`.
4. Call `suggest_outfit(session["selected_item"], wardrobe)`. If `wardrobe["items"]` is empty, the LLM gives general styling advice instead of personalized suggestions. Store the result in `session["outfit_suggestion"]`.
5. If `session["outfit_suggestion"]` is an empty string (LLM failed): set `session["error"]` = "Could not generate an outfit suggestion." Return session. Stop here.
6. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])`. Store result in `session["fit_card"]`.
7. If `session["fit_card"]` is an empty string (LLM failed): set `session["error"]` = "Cannot generate a fit card without an outfit suggestion." Return session.
8. Return session.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
A `session` dict is created at the start of each interaction and passed through the planning loop. Each tool writes its result into the session, and the next tool reads from it — the user never has to re-enter information.

Tracked values:
- `session["selected_item"]` — the listing dict returned by `search_listings` (used as input to both `suggest_outfit` and `create_fit_card`)
- `session["outfit_suggestion"]` — the string returned by `suggest_outfit` (used as input to `create_fit_card`)
- `session["fit_card"]` — the caption string returned by `create_fit_card`
- `session["error"]` — set to an error message string if any tool fails; otherwise `None`

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|| search_listings | No results match the query | Set session["error"] = "No listings found. Try a broader description, a higher price, or remove the size filter." Stop and return session without calling the next tools. |
|| suggest_outfit | Wardrobe is empty | Still call the LLM but prompt it to give general styling advice for the item without referencing a specific wardrobe. Return the advice string and continue. |
|| create_fit_card | Outfit input is missing or incomplete | If `outfit` is an empty string, set session["error"] = "Cannot generate a fit card without an outfit suggestion." Return that string without calling the LLM. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

User query (description, size, max_price, wardrobe)
    │
    ▼
Planning Loop ───────────────────────────────────────────────────┐
    │                                                            │
    ├─► search_listings(description, size, max_price)            │
    │       │ results=[]                                         │
    │       ├──► [ERROR] "No listings found..." ──────────────── ┤
    │       │                                                    │
    │       │ results=[item, ...]                                │
    │       ▼                                                    │
    │   Session: selected_item = results[0]                      │
    │       │                                                    │
    ├─► suggest_outfit(selected_item, wardrobe)                  │
    │       │ wardrobe["items"]=[]                               │
    │       ├──► [FALLBACK] LLM gives general styling advice     │
    │       │       └──► still returns outfit string, continues  │
    │       │                                                    │
    │       │ LLM returns empty string                           │
    │       ├──► [ERROR] "Could not generate outfit." ────────── ┤
    │       │                                                    │
    │       │ outfit_suggestion = "..."                          │
    │       ▼                                                    │
    │   Session: outfit_suggestion = "..."                       │
    │       │                                                    │
    └─► create_fit_card(outfit_suggestion, selected_item)        │
            │ outfit=""                                          │
            ├──► [ERROR] "Cannot generate fit card..." ────────  ┤
            │                                                    │
            │ outfit="..."                                       │
            ▼                                                    │
        Session: fit_card = "..."                                │
            │                                                    └─ all error paths return here
            ▼
        Return session
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I'll use Claude. For each tool, I'll paste that tool's spec block from this planning.md (what it does, input parameters, return value, failure mode) and ask it to implement that one function in `tools.py` using `load_listings()` from `utils/data_loader.py`. Before running it, I'll check that the generated code filters by all three parameters and handles the failure mode I described. Then I'll test it with at least 2 different inputs and confirm the output matches the expected return value.

**Milestone 4 — Planning loop and state management:**
I'll use Claude. I'll paste the Planning Loop section and the Architecture diagram from this planning.md and ask it to implement `run_agent()` in `agent.py`. I'll verify the generated code: (1) branches on the `search_listings` result and does not call all three tools unconditionally, (2) stores values in the `session` dict correctly, and (3) passes `session["selected_item"]` and `session["outfit_suggestion"]` into the next tools without re-prompting the user.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**What FitFindr does:**
FitFindr is an AI agent that takes a user's clothing request and searches a cloth listings dataset to find matching items. Once it finds an item, it suggests how to style it with the user's existing wardrobe, then generates a short, shareable outfit caption. It stops early and tells the user what to change if no listings match their query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent calls `search_listings("vintage graphic tee", size=None, max_price=30.0)`. It scans `listings.json` and filters by price ≤ $30 and keywords matching the description. It returns a list of matching items — e.g., `lst_006` "Graphic Tee — 2003 Tour Bootleg Style" at $24. The agent picks `results[0]` as `selected_item` and stores it in session state.

**Step 2:**
The agent calls `suggest_outfit(selected_item, wardrobe)` using the item from Step 1 and the user's wardrobe (baggy jeans + chunky sneakers). The LLM returns a styled outfit suggestion, e.g., "Wear this with your dark-wash baggy jeans and chunky white sneakers for a 90s streetwear look." The agent stores this in `session["outfit_suggestion"]`.

**Step 3:**
The agent calls `create_fit_card(outfit_suggestion, selected_item)` using the outputs from Steps 1 and 2. The LLM generates a short, Instagram-style caption, e.g., "grabbed this faded bootleg tee for $24 and it goes with literally everything in my closet 🖤". The agent stores this in `session["fit_card"]`.

**Final output to user:**
The user sees all three results: the matched listing (title, price, platform, condition), the outfit suggestion, and the fit card caption.

**Error path:**
If `search_listings` returns `[]`, the agent skips Steps 2 and 3, sets `session["error"]`, and tells the user: "No listings matched your search. Try a broader description, higher price, or remove the size filter."
