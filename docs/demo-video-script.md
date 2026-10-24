# CarbonTruth — demo video script (3–5 min)

**Team Pyragrid · ClimateChain Global Hackathon 2026**
Target length **4:00**. Record screen at 1920×1080. Two assets on screen:
the **deck** (artifact) and the **live prototype** (`python app.py` → http://127.0.0.1:8017).
Voiceover in **bold**; [stage directions in brackets].

> Craft rule we're following (from the animation grammar): **silence before the payoff,
> loudest on the payoff.** The quiet beat is the inflated-claim pause; the payoff is the
> over-credit being rejected and the honest VCC minting.

---

## 0:00–0:25 · Cold open — the problem (deck slide 3)

[Open on the deck, slide 3 "The science is brutal". Let the 94% phantom bar animate.]

**"In 2023, Science looked at 89 million forest-carbon credits. Only six percent
were backed by real carbon. The other ninety-four percent? Phantom — tonnes
someone paid to remove, still in the air. This is a trillion-dollar market, and
it's running on data nobody can trust."**

---

## 0:25–0:50 · The insight (deck slides 4 → 5)

[Advance to slide 4 "Blockchain makes bad data permanent", then slide 5 "Verify once".]

**"Every other team will put a credit on a blockchain and call it transparent. But
a ledger only proves a number didn't change — not that it was ever true. The real
gap is the oracle problem: getting a trustworthy measurement onto the chain in the
first place. CarbonTruth fixes that. One primitive — a Verified Climate Claim.
Verify once. Trusted everywhere."**

---

## 0:50–1:10 · What it is (deck slide 6, let the engine animation play once)

[Slide 6. Press Run on the engine animation; let the lock snap and the receipt stamp.]

**"Raw satellite pixels go in. A cryptographic, unforgeable receipt comes out —
AI-verified, anchored on-chain, and globally unique. And this isn't a mock-up."**

[Beat. Cut to a terminal.]

---

## 1:10–1:40 · It's real — launch the prototype

[Terminal. Type and run:]

```
python app.py
```

[Show the banner, then open http://127.0.0.1:8017 in the browser.]

**"One command, pure Python, no setup. This is the explorer. Up top, it's pulling
live Sentinel-2 scene IDs over our plot straight from Microsoft's open satellite
catalog — real imagery, no API key. The registry is empty. Let's change that."**

---

## 1:40–2:25 · Honest claim → mint (the build)

[Click **▶ Verify honest claim**. Narrate as each stage renders.]

**"Stage one, observe: we compute NDVI from the red and near-infrared bands —
you can see the degraded patch on the left regrowing on the right. Stage two,
model: NDVI becomes biomass becomes CO₂e, against a counterfactual baseline, so we
only credit *additional* carbon. Stage three, verify: three independent estimators —
optical, lidar, and the historical baseline — are fused by inverse-variance
weighting."**

[Gauge fills to 99.3%. Lock/receipt appears.]

**"Ninety-nine point three percent confidence, three of three oracles agreeing —
above our ninety-percent gate. Minted: four thousand ninety-six tonnes, as a
Verified Climate Claim, with its evidence hash on the chain."**

---

## 2:25–2:55 · The payoff — catching fraud (silence, then the hit)

[Click **▶ Verify honest claim** AGAIN. Pause half a beat before it resolves.]

**"Watch what happens if someone tries to mint the same tonne twice…"**

[Result: DOUBLE-COUNT BLOCKED.]

**"Blocked. Same place, same time — same fingerprint. One token per fingerprint,
so double counting isn't discouraged. It's impossible."**

[Now click **▶ Verify inflated claim**. Let the gauge drop to 32% red.]

**"And here's a project claiming three times the carbon it actually has — the kind
of over-credit Science exposed. Independent consensus says thirty-two percent.
Rejected. No credit minted. The fraud never reaches the market."**

---

## 2:55–3:20 · Integrity you can audit

[Point to the "chain intact" badge; optionally retire a credit.]

**"Every block hashes the one before it, so the whole history is tamper-evident —
and anyone can retire a credit exactly once, forever. This same logic is a real
Solidity contract in the repo, ready for any EVM testnet."**

---

## 3:20–3:50 · Why it wins (deck slides 9 → 10)

[Back to deck. Slide 9 "One primitive, all four tracks", then slide 10 market.]

**"Because it's a verification layer, not a marketplace, the same receipt works for
carbon, clean energy, supply chains, and climate data — all four tracks, one
platform. We don't sell tonnes. We sell trust: roughly a dollar-fifty a credit, at
near-zero marginal cost, into a market the UN's Article 6.4 now *mandates*
verification for."**

---

## 3:50–4:00 · Close (deck slide 13)

[Slide 13 "Every tonne, verified once".]

**"CarbonTruth, from team Pyragrid. Every tonne — verified once, trusted
everywhere. Thank you."**

---

### Shot checklist
- [ ] Deck slides 3, 4, 5, 6, 9, 10, 13 cued and tested
- [ ] `python app.py` runs clean; ledger reset (empty registry) before recording
- [ ] Browser zoom so NDVI grids + gauge are clearly visible
- [ ] Do the three clicks in order: honest → honest(blocked) → inflated(rejected)
- [ ] Record the live Sentinel-2 strip while online
- [ ] Keep total under 5:00; aim 4:00

### One-line submission blurb
*CarbonTruth (team Pyragrid) is the SSL certificate for climate data: an AI + multi-oracle
verification layer that turns satellite data into unforgeable, retire-once carbon credits —
catching the over-crediting that peer-reviewed science found in 94% of forest credits.*
