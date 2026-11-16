# Unit 2 Review — Presentation Script (Team of 3, ~9 min)

Deck: Unit2_ML_Robust_Ocean_Temperature.pptx

---

## PRESENTER 1 — Framing & Data (Slides 1-4, ~2.5 min)

### Slide 1 — Title
"Good morning. Our Unit 2 problem is predicting ocean temperature from salinity
across 60-plus years of data, using outlier-proof regression so that faulty
sensors don't corrupt the model. We solved it on the real CalCOFI ocean survey
archive."

### Slide 2 — Problem Statement
"That's the problem statement as given. What makes it hard is that a 72-year
archive is stitched together from many ships, crews and instrument generations.
Thermistors drift, sensors get fouled, bottles sit in the sun — and crucially, a
faulty reading is usually still a PHYSICALLY PLAUSIBLE NUMBER. You can't filter
it out with a range check.

One design decision governs everything: every model is trained on contaminated
data, then scored on the same clean held-out test set. That's the only honest
way to measure corruption."

### Slide 3 — The Data
"This is real data — 895,371 bottle records from March 1949 to May 2021.
844,748 have both temperature and salinity. CalCOFI's own quality codes flag
38,593 of them, and 934 are physically impossible — you can see a 99-degree
reading in the archive, which is a stuck sensor, not seawater. After screening,
806,108 clean rows remain. Correlation is minus 0.5 — real, but clearly
non-linear, so we use basis functions."

### Slide 4 — Concept Map
"Here's how the five Unit 2 concepts map onto the project. Maximum likelihood
gives our baseline, basis functions handle the curve, Huber is the primary
deliverable, ridge is the MAP estimate with a Gaussian prior, and Bayesian
regression gives us error bars. My teammate will take the theory."

---

## PRESENTER 2 — The Concepts (Slides 5-7, ~3 min)

### Slide 5 — MLE reduces to Least Squares
"Start with maximum likelihood. Assume Gaussian noise, write the log-likelihood,
and every term except the sum of squared errors is constant — so maximising
likelihood IS minimising squared error. That's the Unit 2 result.

And that's exactly where it breaks. The squared term means influence grows
without limit. A row that's 20 degrees wrong pulls 400 times harder than one
that's 1 degree wrong. We measured it: OLS on clean data has essentially no
bias, but corrupt 10% of the rows and it acquires a PLUS 1.1 DEGREE SYSTEMATIC
WARM BIAS. It now reports an ocean that's over a degree too warm, everywhere."

### Slide 6 — Huber Loss  [PRIMARY DELIVERABLE]
"Huber loss fixes this. Quadratic near zero, linear beyond delta — so it stays
efficient on good data but a bad row's influence is BOUNDED. It's equivalent to
assuming heavy-tailed noise instead of Gaussian: large errors are expected, not
impossible.

Look at the right-hand panel. The red curve is OLS trained on faulty data —
lifted clear of the true data. The green curve is Huber on THE SAME FAULTY DATA,
and it sits right on top of the dotted line, which is the OLS fit from perfectly
clean data. Huber recovered the truth it was never shown."

### Slide 7 — Ridge & Bayesian  [THE KEY FINDING]
"Now the result we didn't expect. Ridge is MAP estimation with a Gaussian prior
on the weights. Bayesian regression gives a full posterior and honest error
bars. Both are excellent — but neither helped here.

At 10% contamination, OLS, Ridge and Bayesian all land on the SAME warm bias:
plus 1.109, plus 1.113, plus 1.109. Huber, on identical data, holds at minus
0.14.

The reason: the ridge penalty acts on the weights, never on the residual. A
faulty row keeps its full quadratic pull. Regularisation fixes overfitting; only
a robust loss fixes contamination. They solve different problems — and that
directly answers the discussion question from the lecture."

---

## PRESENTER 3 — Implementation & Results (Slides 8-10, ~3 min)

### Slide 8 — Implementation
"Implementation is a two-stage defence. Stage one is a physical gate for
impossible inputs. Stage two is the robust fit — degree-5 polynomial basis,
RobustScaler, then HuberRegressor.

Two decisions mattered. First, StandardScaler is ITSELF non-robust — one extreme
row distorts the mean and sigma used to scale everything else, so we used median
and IQR instead. Second, Huber protects against faults in the target; gross
faults in the INPUT are leverage points, which is why stage one exists. And our
injected faults deliberately stay inside the physical range, so no range check
can catch them — only the loss function can."

### Slide 9 — Results
"Results. Everything trained with 10% faulty sensors, scored on the same clean
test set.

OLS carries a plus 1.109 degree warm bias. Huber holds at minus 0.141 — SEVEN
AND A HALF TIMES LESS. At 30% contamination Huber's error is 17% lower than OLS.
And Huber's outlier mask caught 99.4% of every injected fault, so it doubles as
a sensor-QC detector for free.

One honest limitation: salinity alone explains only about 41% of temperature.
That's real ocean physics — the temperature-salinity curve is multi-valued
across water masses. Our project measures robustness, not maximum R-squared."

### Slide 10 — Conclusion
"To close — a physical gate plus Huber regression predicts ocean temperature
across 72 years of real survey data and stays essentially unbiased even when one
training row in ten comes from a faulty sensor. Faulty sensor readings do not
corrupt the predictions.

Next step for Unit 3 is replacing the polynomial basis with kernel functions and
fitting an SVR on the same data. Thank you — happy to take questions."

---

## LIKELY QUESTIONS

Q: "Why is R-squared only 0.41?"
A: "Because salinity alone is genuinely ambiguous — the same salinity occurs at
   different temperatures in different water masses. Adding depth would resolve
   it. The problem statement asked us to predict from salinity, and the goal was
   robustness, not R-squared."

Q: "Why not just delete the outliers?"
A: "We do, for the impossible ones — that's stage one. But the dangerous faults
   are physically plausible numbers. You can't detect them by range; you need a
   loss function that bounds their influence. And Huber's mask then identifies
   them at 99% recall."

Q: "Why delta = 1.35?"
A: "It's the standard choice — it retains about 95% of OLS efficiency under
   clean Gaussian noise, so robustness is nearly free. We flagged tuning it as
   future work."

Q: "Are the faults real or injected?"
A: "Both. The archive's 38,593 QC-flagged rows are real. To measure degradation
   at controlled rates we inject additional warm-biased faults that stay inside
   the physical range — so no range check can catch them. That's the hard case."

---

## KEY NUMBERS — MEMORISE THESE

  895,371    bottle records read (1949-2021, 72 years)
  844,748    paired temperature + salinity
   38,593    QC-flagged by CalCOFI (4.57%)
  806,108    clean rows after screening
    -0.505   correlation(salinity, temperature)
   +1.109 C  OLS warm bias at 10% contamination
   -0.141 C  Huber warm bias  -> 7.5x less
     99.4%   of injected faults caught by Huber
       17%   lower RMSE than OLS at 30% contamination
      1.35   Huber delta
