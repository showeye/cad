# Szyb Prezydent: the choice, the sources and the measurements

Research date: 14 November 2026. This file records why this shaft was chosen, which figures
are published, which were measured from photographs and how far each can be trusted. The
figures themselves live in `Prototype` in [`src/prezydent/model.py`](../src/prezydent/model.py),
where each one is marked [P] (published) or [M] (measured).

## 1. Why this shaft

The brief: the most iconic mine shaft of Silesia that also looks good once printed.

| Candidate | What it is | As a print |
|---|---|---|
| **Prezydent, Chorzów** (1933) | The only reinforced-concrete headframe in Poland: a ladder-like trunk, two splayed struts, two red sheaves on top. On the Industrial Monuments Route and ERIH. [1][2][3] | Members are 0.4 to 2 m thick, so at 1:250 every one of them is at least 1.6 mm. The structure can be printed at its true proportions. **Chosen.** |
| Warszawa II, Katowice (1920s) | Riveted steel lattice, about 40 m, the emblem of Muzeum Śląskie. [5] | Probably the most widely recognised. Its lattice members would come out well under a millimetre at 1:250 (an estimate, not measured): they must be thickened several times over, and the result is a caricature on a filament printer. Better suited to resin or etched metal. |
| Krystyna, Bytom (1929) | Brick hammer-head tower, 57 m. [4] | Prints easily, but it is a plain block: its character is in brickwork and windows, which is surface texture, not form. Under renovation. |
| KWK Polska, Świętochłowice | A pair: a tower-type headframe of 1908 and a rare four-legged trestle of 1889-91. [6] | Two towers to make, and the trestle is steel lattice again. |

Prezydent is the one case where "iconic" and "prints well" agree: the real thing is already
made of a few thick straight members, and its silhouette (an A from the west, a leaning
ladder from the south, red wheels on top) reads at any size.

## 2. Published figures

From the heritage record at zabytek.pl [1], which summarises the 1990 record card, unless
another source is named:

- The platform that carries the sheaves is at **42 m**; the headframe is "approx. 46 m" high.
  Wikipedia gives 42 or 42.5 m as the total height. [2]
- The struts stand **about 15 m** apart; their footings are **21 m** from the tower axis.
- The posts are tied by beams "at a dozen or so levels, starting from 4.45 m up to approx. 40 m".
- Two rope sheaves of **5.5 m** diameter, side by side, "over 2 m" apart. [1][2][3]
- Viewing terrace at **34 m**, reached by 201 steps; opened in 2014. [2]
- Built 1932 or 1933 for the Skarboferm company, designed by Ryszard Heileman of Katowice.
  Shaft 234 m deep, a 10-ton skip. Register entry A/228/08. [1][2][3]

No plan, section or member size is published. The record card itself (E. Szady, 1990) was
not seen.

## 3. Measurements from photographs

Three photographs from Wikimedia Commons were measured with a pixel grid:

- **south**: `Betongerüst Schacht Jacek.jpg`, a long-lens view from the south-south-east,
  verticals parallel. The main source for levels and for everything along X.
- **west**: `Chorzów wieża szybu Prezydent W 2026.jpg`, square-on from the engine-house side.
  The source for everything across (Y) and a second check on the levels.
- **top**: `Chorzów wieża szybu Prezydent aerial 2026 (2).jpg`, a drone view straight down.
  The source for the deck plan, the sheave positions and their slots.

The photographs are linked from the Commons category [7] and are not copied into this
repository.

**Method.** In the south view every vertical line has its own linear scale, so levels were
read along the nearest corner post. The view direction is 21° off square (from the ratio of
the head's two visible faces, whose plan ratio the top view gives). Horizontal sizes on the
south face are divided by cos 21°, sizes across by sin 21°.

**Calibration.** With the deck at 42 m [P], the south view comes out at 40 px/m, and these
then agree:

| Check | From the photo | Published |
|---|---|---|
| Strut footing to the tower axis | 21.2 m | 21 m |
| Sheave across its rim | 5.8 m | 5.5 m, read as the rope tread (the rim flanges add about 0.15 m a side) |
| Sheaves apart (top view, scaled by that rim) | 2.09 m | "over 2 m" |
| Top of the crane beam over the sheaves | 46.3 m | "approx. 46 m" |

The west view confirms the levels: the beams at 9.55 m and 12.5 m fall at the same fractions
of the height in both photographs.

**What does not agree.**

1. *The lowest beam.* The record says the beams start at 4.45 m. In the south view the
   south and east faces have a beam at about 2.25 m and the next at 5.9 m; in the west view
   the strut-side face has none below 9.55 m. Either the record uses another datum or it counts differently.
   The model follows the photographs.
2. *Struts apart.* The photographs give 13.8 m between strut centres at the ground, the
   record "approx. 15 m". The model uses 15 m between centres; the record may mean outer
   faces.
3. *The overall scale.* The south and west views put the deck height at 7.4 to 7.9 times the
   width of the head, and the top view makes that width 0.93 of a sheave's rim. If the 5.5 m
   of the sheaves were their rim, the deck would be at 38 to 40 m, not 42.
   The model takes the record's 42 m and lets the rim be 5.8 m. Until one length is measured
   on site, every figure marked [M] carries about ±5 %, and the whole model could be up to
   5 % too large in plan.

One tape or laser measurement on site settles point 3: the trunk should be **5.8 m** along
the strut direction and **5.1 m** across, outside to outside, above the piers.

## 4. What the structure is

Seen from the model's axes (X towards the strut feet, Z up):

- **Trunk**: four corner posts 0.65 × 0.6 m on a 5.8 × 5.1 m plan, tied by beams at ten
  levels (2.25 to 31.8 m). The two strut-side posts are 2.2 × 1.1 m walls ("piers") up to
  19.2 m and taper below 9.3 m; the two others widen slightly towards the ground.
- **Struts**: two, leaning 23° towards the engine house and 8.5° towards each other, 1.45 m
  deep, 2.0 m wide at the ground and 1.4 m where they enter the head. Each stands on a wedge
  footing about 4 × 5 m.
- **Brace frame** at 19.2 m: a cross beam between the struts and a beam from each strut to
  its pier, all with haunches.
- **Head**: the terrace slab at 34 m, an open storey above it, then a box from 37.8 m to the
  deck at 42 m that reaches 4.3 m beyond the trunk, towards the struts, which carry its far
  end. Under that end is a sloping hood above the window through which the ropes left for
  the engine house.
- **Sheaves**: two, 2.1 m apart, axles 0.5 m above the deck, lower halves hanging in slots.

## 5. True to scale, or simplified?

At 1:250 the tower is 168 mm to the deck and about 185 mm overall on its plinth. `fidelity()`
in the model lists what printing does to the thin members:

| Member | Real | True to scale | Printed |
|---|---|---|---|
| Post, thinner side | 0.60 m | 2.4 mm | 2.4 mm |
| Tie beam, depth | 0.50 m | 2.0 mm | 2.0 mm |
| Tie beam, width | 0.40 m | 1.6 mm | 1.6 mm |
| Brace beam, width | 0.90 m | 3.6 mm | 3.6 mm |
| Strut, depth | 1.45 m | 5.8 mm | 5.8 mm |
| Sheave, thickness | 0.33 m | 1.32 mm | 1.6 mm |
| Sheave, rim | 0.22 m | 0.88 mm | 1.6 mm |
| Sheave, spoke | 0.12 m | 0.48 mm | 1.2 mm |

So: **the concrete of 1933 is at true scale; the steel fittings are not and cannot be.** A
railing tube is 0.2 mm at this scale. 1:250 is also the smallest scale at which this holds:
below it the tie beams fall under 1.6 mm and the model thickens them (a test covers this).

Simplifications in version 0.1.0, beyond the fittings:

- The box under the deck is solid. In reality it is a room, open to the terrace below.
- The terrace is a plain slab, without its rope openings and edge beams.
- Left out so far: deck railings, the crane beam over the sheaves (the "46 m"), the flagpole,
  the two small balconies, the brick infill panel on the east face, the corbels at 10 m.
- Left out on purpose: the steel stairs, mesh and glazing of the 2014 conversion. The model
  shows the structure, not the tourist fit-out.
- Sheaves have 8 spokes; the real ones have more, thinner ones.

## 6. As a souvenir

For it:

- The site already draws visitors: it is on the Industrial Monuments Route and ERIH, open
  daily, next to the Sztygarka restaurant complex, lit at night. [3]
- The shape is unlike any other headframe, so it cannot be mistaken for a generic "mine".
- Three colours that are the real colours: pale concrete, red wheels, dark ground. The
  Snapmaker U1 prints four.
- About 76 cm³ of solid plastic before infill; a desk object 185 mm tall on a 120 × 92 mm
  plinth.
- A quick search found no printed model of this tower on sale. That is an absence of search
  results, not proof of an empty market.

Against it, or still open:

- It is a local icon: strong in Chorzów and the Katowice area, weaker elsewhere than the
  Muzeum Śląskie tower.
- It is static. The earlier Carnall concept in this repository bet on motion.
- Nothing is printed. The open storeys, the 18 mm beam bridges and the thin upright sheaves
  need a test print before anything is promised.
- Rights were not checked. The designer's dates, the city's ownership of the tower and the
  use of its name on a product need a look before sale.

## 7. Sources

1. [National Heritage Board: headframe of the Prezydent shaft](https://zabytek.pl/en/obiekty/chorzow-wieza-wyciagowa-szybu-prezydent)
2. [Wikipedia (pl): Szyb Prezydent](https://pl.wikipedia.org/wiki/Szyb_Prezydent) and
   [Wikipedia (en): Prezydent Shaft](https://en.wikipedia.org/wiki/Prezydent_Shaft)
3. [Industrial Monuments Route: "President" Shaft](https://www.zabytkitechniki.pl/en-us/Poi/Pokaz/1689/57/president-shaft)
4. [National Heritage Board: headframe of the Krystyna shaft](https://zabytek.pl/en/obiekty/bytom-wieza-wyciagowa-szybu-krystyna)
5. [dzieje.pl: the Warszawa II tower of Muzeum Śląskie](https://dzieje.pl/node/168009)
6. [National Heritage Board: two headframes of the Polska mine](https://zabytek.pl/en/obiekty/swietochlowice-dwie-wieze-wyciagowe-d-kopalni-polska)
7. [Wikimedia Commons: Prezydent winding tower](https://commons.wikimedia.org/wiki/Category:Prezydent_winding_tower)
