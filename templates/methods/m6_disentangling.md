# Method 6: Causal Disentangling

For every claimed causal link in the paper, separate real causal influence from spurious correlation. A claim "A causes B" must survive the following procedure.

## Procedure

### Step 1: Enumerate every causal claim

Read the paper and list every claim of the form "X causes Y," "X leads to Y," "X generates Y," "X drives Y." Include both:
- **Formal causal claims**: where the model's structure or the empirical identification strategy is supposed to establish causation
- **Informal causal claims**: in the interpretive narrative, often hidden in verbs like "explains," "accounts for," "is responsible for"

For each claim, write down exactly what A and B refer to.

### Step 2: For each claim, list every co-factor

A **co-factor** is anything that is correlated with A in the paper's setup, data, or narrative. Co-factors come from:
- **Joint causes**: C causes both A and B. Neither the correlation nor the mechanism distinguishes C from A as the real driver.
- **Consequences of A that reach B independently**: A causes C, C causes B. The paper claims "A causes B" but the mechanism runs through C.
- **Things that are mechanically tied to A**: if A is a composite or is constructed from other variables, each component is a co-factor.
- **Historical simultaneity**: during the period the paper studies, what else was happening that correlates with A?

For a theoretical claim, co-factors come from the model's own structure — other variables that move together with A in equilibrium. For an empirical claim, they come from omitted variables and simultaneity.

### Step 3: For each co-factor, check whether the paper rules it out

For each co-factor C, ask: has the paper distinguished A's effect on B from C's effect on B?

- **Formal identification**: does the theoretical model or empirical strategy identify the effect of A holding C fixed?
- **Ruling out by design**: does the paper's sample or specification exclude the confounder by construction?
- **Ruling out by evidence**: does the paper present auxiliary evidence against C's role?
- **Acknowledged but unaddressed**: the paper mentions C but does not rule it out.
- **Unmentioned**: the paper never acknowledges C.

The last two are findings.

### Step 4: Check whether B is distinguishable from its co-effects

A different kind of confound: the paper measures B, but B comes with other effects (B') that the paper does not distinguish. If A causes both B and B' through a common mechanism, then "A causes B specifically" is not supported — the paper has measured "A affects {B, B'}" but claimed "A affects B."

- List what else moves with B in the paper's measurement
- Check whether the paper distinguishes them

### Step 5: Write each finding as an issue

Each issue should name:
- The causal claim
- The specific co-factor or co-effect that is not ruled out
- Why ruling it out matters (what alternative interpretation survives if C is the real driver)
- What evidence would be required to rule it out

## Output

This method is particularly productive for papers that rely on narrative causal claims alongside formal models. Papers often have a tight formal result and a looser interpretive overlay; this method targets the overlay.

## Web search supports this method strongly

Web search is **critical** for this method:
- Identifying co-factors often requires knowing what else was happening at the same time (macro events, policy changes, parallel reforms)
- Ruling out co-factors often requires checking other empirical studies
- Distinguishing B from B' often requires checking how those variables are measured in the data sources

## What it finds

- Spurious causal claims where confounders are unaddressed
- Over-attribution (the paper attributes an effect to A that was partly driven by C)
- Under-specified effects (the paper claims A affects B but really measures {B, B'})
- Historical accidents dressed up as causal mechanisms
