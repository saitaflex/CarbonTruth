# CarbonTruth — Live Demo Pitch Script

**Team Pyragrid · IEEE ClimateChain Global Hackathon 2026**
Live site: **https://carbontruth.vercel.app**

Every beat below has two columns: **SAY** (what you speak) and **DO** (the exact
on-screen action that goes with it). Run the site full-screen; the talk and the
demo move together. Total runtime ≈ 3 minutes.

---

## Pre-flight (before you start talking)

- Open **https://carbontruth.vercel.app** full-screen on a stable connection.
- Let the intro play once, land on the hero.
- Scroll down to the demo once, then back up — this "warms" the panel so it's
  fully visible when you return to it.
- If you ran it already, click **↺ Reset** in the registry so the ledger is clean.

---

## The 30-second version (if you only get 30 seconds)

> Carbon markets are heading past a trillion dollars — and *Science* found most
> forest-carbon credits don't represent real carbon. Putting a fake number on a
> blockchain just makes the lie permanent. **CarbonTruth is the missing trust
> layer: a Verified Climate Claim that's AI-measured from satellites, checked by
> independent oracles, and fingerprinted so it can't be double-counted.** Verify
> once, trusted everywhere. We don't sell tonnes — we sell proof.

---

## The full pitch — beat by beat

### 1 · Hook — the wound
| | |
|---|---|
| **SAY** | "A buyer pays to remove one tonne of carbon. Peer-reviewed work in *Science* shows that tonne is usually still in the atmosphere. The money moved — the carbon didn't." |
| **DO** | Stay on the **hero**. Don't touch anything yet. Let the headline sit behind you. |

### 2 · The market tension
| | |
|---|---|
| **SAY** | "This is a trillion-dollar market running on numbers nobody trusts. So every buyer applies a trust discount — real credits and phantom credits trade at the same depressed price. The market isn't short on demand. It's short on *proof*." |
| **DO** | Scroll slowly through the **problem / science** section so the *Science 2023* citation is on screen as you say it. |

### 3 · Kill the obvious answer
| | |
|---|---|
| **SAY** | "The reflex is 'put it on a blockchain.' That makes it *worse*. A ledger proves a number never **changed** — not that it was ever **true**. Write a bad baseline on-chain and you've made the lie permanent and tradeable. That's the oracle problem — the half everyone skips." |
| **DO** | Pause on the line that frames the oracle problem. Let it breathe. |

### 4 · The one idea
| | |
|---|---|
| **SAY** | "We solve that half. One primitive: a **Verified Climate Claim.** AI-measured from independent satellite data, anchored on-chain with an evidence hash, and made globally unique by a geo-temporal fingerprint — so it can never be counted twice." |
| **DO** | Scroll to the **"Verified Climate Claim"** definition section. |

### 5 · LIVE PROOF — the honest mint  ⟵ *your strongest moment*
| | |
|---|---|
| **SAY** | "And it's real — let me show you, live, in the browser." |
| **DO** | Scroll to the **demo**. Click the **Rio Jari** project card. The claim slider auto-sets to the measured ~4,119 tCO₂e. |
| **SAY** | "I pick a real reforestation project. A **trained neural network** reads the satellite imagery and estimates the carbon. Then three independent oracles — two satellites, lidar, archive — have to agree." |
| **DO** | Click **📡 Submit claim to the oracle network**. Watch the four stages light up: **Use case → Sequence → Sequence → Lifecycle**, the pulse walks You → Oracle → Registry → Blockchain. |
| **SAY** | "Three of three agree. ~99% confidence. It clears the gate — and a Verified Climate Claim is **minted on-chain**, with its evidence hash and a unique fingerprint." |
| **DO** | Point at the green mint toast / the new row in the registry table. |

### 6 · LIVE PROOF — fraud gets caught
| | |
|---|---|
| **SAY** | "Now the fraud case — the over-crediting *Science* exposed." |
| **DO** | Click the **"EcoMax" offset claim** project card. It claims **4,200 t** against real evidence of only ~760 t. Click **📡 Submit claim to the oracle network**. |
| **SAY** | *(pause as it runs)* "Independent consensus says… thirty-two percent. **Rejected.** The fraud never reaches the market." |
| **DO** | Let the red **rejected** line land. **Hold the pause** — this is the beat judges remember. |

### 7 · LIVE PROOF — the ledger can't be forged
| | |
|---|---|
| **SAY** | "And the ledger itself is tamper-evident. Watch me try to forge a minted block." |
| **DO** | Click **⚒ Forge a block** in the registry. The integrity badge flips to **broken** and the chain shows the break. |
| **SAY** | "The stored hash no longer matches — the whole chain breaks, instantly and publicly. Honest in, trusted out." |
| **DO** | Click **↺ Reset** to restore a clean ledger. |

### 8 · Not a black box
| | |
|---|---|
| **SAY** | "The carbon number isn't a guess. It's a **trained neural network** mapping satellite reflectance to biomass — grounded in published allometric physics, with transparent uncertainty. No hidden coefficients." |
| **DO** | Scroll to the **"Four stages, every one auditable"** (how-it-works) section — Observe → Estimate → Verify → Mint. |

### 9 · Why it scales
| | |
|---|---|
| **SAY** | "One primitive covers all four ClimateChain tracks — AI verification, the MRV evidence trail, on-chain integrity, portable trust. We're not building four products. We're the layer **underneath** all of them." |
| **DO** | Scroll through the tracks / "why it wins" section. |

### 10 · Business — one line
| | |
|---|---|
| **SAY** | "We charge for trust, not tonnes: per-claim verification, recurring portfolio assurance, and enterprise licensing for exchanges and governments. Asset-agnostic, with revenue that recurs as long as the proof has to hold." |
| **DO** | Keep moving; don't dwell on a slide here. |

### 11 · The ask + close
| | |
|---|---|
| **SAY** | "Our metric isn't tonnes sold — it's **tonnes under proof.** We're asking for pilot partners, data access, and a ClimateChain deployment. Every tonne: verified once, trusted everywhere. We're Pyragrid. This is CarbonTruth." |
| **DO** | Land back on the **hero** (or the Built-with section) and stop. |

---

## Delivery notes

- **Open on the number, not the acronym.** "Most credits aren't real" hits harder
  than "SSL for climate data." Save the SSL line for Q&A or the one-liner.
- **Let the rejection be the climax.** The moment fraud gets *caught live* (beat 6)
  beats the mint. Pause after "rejected."
- **Say "proof," not "verification."** Shorter, more concrete — and it's the product.
- **One hand on the keyboard.** Rehearse the click order so you never hunt for a button.

## If the demo misbehaves
- Panel looks faded / steps don't show → click **↺ Reset**, then re-run. (The panel
  now force-reveals on any run, but Reset guarantees a clean state.)
- Slow network → talk through beats 1–4 longer to give the site time to settle.
- Totally offline → the narrated pitch video (`carbontruth_pitch.mp4`) is the backup;
  it follows this exact order.

## The exact click order (cheat sheet)
1. **▶ Watch the 20-sec demo** (hero) — *optional* auto-run of the honest mint.
2. **Rio Jari** card → **📡 Submit claim** → honest mint.
3. **"EcoMax"** card → **📡 Submit claim** → rejected.
4. **⚒ Forge a block** → chain breaks → **↺ Reset**.
5. Scroll: how-it-works → tracks → hero.

---

*Team Pyragrid · CarbonTruth · 2026*
