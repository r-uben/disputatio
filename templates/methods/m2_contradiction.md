# Method 2: Interrogation by Contradiction

Find places where the paper contradicts itself. The prosecutor does not argue — the prosecutor asks questions that force the paper's own claims to betray each other.

## Procedure

1. **Extract claims.** Read the paper and list at least twenty concrete claims it makes. A claim is a statement the author commits to: equations, propositions, numerical values, assumed conditions, methodological rules, interpretive statements. Include both the setup and the results. Include footnotes — contradictions often hide there.

2. **Pair-check for direct contradiction.** For every pair of claims, check whether they can both be true at the same time. Cases:
   - **Direct**: The paper asserts X in one place and not-X in another. Rare but devastating.
   - **Numerical**: Two values the paper cites are inconsistent with each other (e.g., a parameter is defined as 0.04 in Section II and 0.05 in Section III).
   - **Definitional**: A term is defined one way in the setup and used another way later (e.g., a hazard rate used as a probability).

3. **Pair-check for implicational contradiction.** For every pair of claims (X, Y), check whether X logically implies something that contradicts Y. Cases:
   - X implies Z; paper claims not-Z.
   - X holds only under condition C; paper applies X in a context where C fails.
   - X is a special case of a more general claim; the general claim is violated elsewhere.

4. **Search for hidden premises.** If no contradiction surfaces from the explicit claims, identify the **implicit premise** that, combined with the explicit claims, produces a contradiction. For example: the paper assumes rational expectations (implicit) but also assumes the agents hold biased beliefs about the central bank (explicit). Naming the implicit premise is itself a finding.

5. **Formulate each contradiction as a question.** Not "this is wrong." Not "the author contradicts themselves." A question that the author cannot answer without abandoning one claim:
   - *"If X holds in Section I, how can not-X be true in Section III?"*
   - *"The paper defines θ as a Poisson hazard. How is θ=0.5 then interpreted as a 50% annual probability?"*
   - *"If the central bank has no commitment device, how can it promise future forward guidance?"*

6. **Write each contradiction as an issue.** Include:
   - The two claims (with exact quotes and locations)
   - The logical path from them to the contradiction
   - The formulated question
   - Which claim must be dropped or revised to resolve it

## What it finds

- Self-contradictions between theory and empirics
- Hidden premises smuggled into results
- Numerical inconsistencies between sections
- Scope violations (results applied outside their stated conditions)

## What it does not find

- Claims that are wrong about the external world (use Method 6 for that)
- Claims that are weakly justified but not contradictory (use Method 3 or 5)
- Claims that are too strong but internally consistent (use Method 4)
