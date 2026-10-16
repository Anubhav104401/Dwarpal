---
fingerprint: 2273758267da96e5
---
An `__init__.py` file turns a folder into a Python **package** (§4.2): a folder of modules that can be imported as one unit, as in `import dwarpal_api`. Whatever is written in it runs the first time the package is imported. This one holds only a docstring, but it is the natural place to see how the whole API service is laid out.

The API is split into four **layers**, each in its own sub-package. A layer may use the layers listed *above* it in this table, but never the ones below it:

| Layer | Folder | What lives there | Allowed to use |
| :-- | :-- | :-- | :-- |
| Domain | `domain/` | the rules: identifiers, keys, policies, the decision engine, the session state machine | nothing outside itself — no network, database, file or clock |
| Adapters | `adapters/` | the code that talks to the outside world: PostgreSQL, Valkey, the inference service, signing keys | the domain |
| Use cases | `app/` | the steps of a verification, each written once | the domain and the adapters |
| HTTP | `http/` | turning web requests into use-case calls, and their results into responses | the use cases |

!!! kid "Explain like I'm six — a restaurant"
    The **domain** is the recipe book: it says what a good dish is, but never touches a stove. The **adapters** are the fridge, the oven and the delivery van. The **use cases** are the chef, who follows a recipe using the fridge and the oven. The **HTTP layer** is the waiter, who takes orders and brings plates but never cooks.

This shape is often called **hexagonal architecture**, or "ports and adapters" (Part 3, Choice 10). Its payoff is easy to see in the tests: the rules that decide whether a child gets through are plain Python, so their tests — some of which try hundreds of generated cases each — finish in about two seconds, with no database, network or clock involved.

@@ 1
The package docstring — what the service offers. Tools such as `help(dwarpal_api)` and code editors show this text:

- the **relying-party API**, which websites use to create verification sessions and read their results;
- the **flow API**, which the hosted verify page uses while a person takes the check;
- the **console API** for the admin website, which arrives in Phase 4 (the platform phase of the roadmap);
- and inside them, the **decision engine** and the signer of **age tokens**.

!!! real "Real world — the plan said `modules/`"
    The Stage 3 design sketched one sub-folder per feature, under `modules/`. While building Phase 1, the code turned out clearer when organised by *layer* instead: one verification feature runs through all four layers, and the layers are what tests and reviewers care about. The Phase 1 report records this change.
