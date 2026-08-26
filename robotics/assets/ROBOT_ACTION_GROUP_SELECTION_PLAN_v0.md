Yes—this makes strong sense. It restores the interpretability of Gym-Anything’s tiers while retaining the more sophisticated capability-mediated coverage model.

The essential adaptation is:

> Every tier must select action groups by their marginal capability-mediated coverage, not by their individual economic value.

## Sequential formulation

Let \(S_{t-1}\) be everything selected before tier \(t\). For a target slice \(Q\)—the economy, a strategic domain, a STEM domain, an SOC group, or an occupation—define:

\[
F_Q(S)
=
\frac{
\sum_a V_{Q,a}y_a(S)
}{
\sum_a V_{Q,a}
},
\]

where:

- \(V_{Q,a}\) is action \(a\)’s value inside slice \(Q\).
- \(y_a(S)=1\) when all robot and physics requirements of \(a\) are supplied by selected set \(S\).

The marginal gain of adding bundle \(T\) is:

\[
\Delta_Q(T\mid S)
=
F_Q(S\cup T)-F_Q(S).
\]

Each tier selects a new batch \(T_t\), excludes already selected groups, and then freezes it:

\[
S_t=S_{t-1}\cup T_t.
\]

## k1: Economic core

Choose \(B_1\) action groups that maximize total economic coverage:

\[
T_1
=
\arg\max_{\substack{T\subseteq A\\|T|=B_1}}
F_{\mathrm{economic}}(T).
\]

This is not “select the \(B_1\) highest-GDP actions.” A lower-value action may be preferable if its capability bundle covers many high-value actions.

## k2.1: Strategic domains

Let:

\[
D_{\mathrm{strategic}}
=
\{
\text{healthcare},
\text{education},
\text{protective services},
\text{transportation}
\}.
\]

Conditioned on k1, select action groups that fill uncovered strategic activity.

A balanced formulation is:

\[
T_{2.1}
=
\arg\max_{|T|=B_{2.1}}
\min_{d\in D_{\mathrm{strategic}}}
F_d(S_1\cup T).
\]

Alternatively, reproduce the original paper more literally by giving each domain a fixed sub-budget and optimizing its marginal coverage separately.

The maximin version is useful because strategic actions already covered by k1 need no redundant slots.

## k2.2: STEM and research

Similarly, for:

\[
D_{\mathrm{STEM}}
=
\{
\text{architecture/engineering},
\text{computer/mathematical},
\text{life/physical/social science}
\},
\]

solve:

\[
T_{2.2}
=
\arg\max_{|T|=B_{2.2}}
\min_{d\in D_{\mathrm{STEM}}}
F_d(S_2\cup T).
\]

Again, the objective is incremental coverage after k1 and k2.1.

## k3: SOC-major-group diversity

Cycle through the 22 SOC major groups. For each group \(g\), select the action group or small batch with the greatest marginal capability-mediated coverage:

\[
a_g^*
=
\arg\max_{a\notin S}
\Delta_g(\{a\}\mid S).
\]

After selecting \(a_g^*\), update \(S\) before processing the next group. Repeat round-robin until the k3 budget is exhausted.

The SOC order and tie-break rules must be frozen—for example:

1. Start with the least-covered SOC group.
2. Break equal coverage by larger uncovered economic mass.
3. Break remaining ties by stable action-group ID.

This is better than blindly assigning five actions per SOC group, because an action selected earlier may already cover substantial activity in several groups.

## k4: Niche occupation-specific actions

One correction: k4 should not literally select one action from every occupation unless the budget supports hundreds of slots.

The original k4 meant products unique to specific occupations or domains. The robotics analogue is action groups that are:

- Concentrated in one or a small number of occupations.
- Economically or operationally important within those occupations.
- Poorly covered by the earlier broad tiers.
- Dependent on unusual capabilities that generic actions do not supply.

Define an occupation-specific candidate set, for example:

\[
A_{\mathrm{niche}}
=
\left\{
a:
\left|
\{o:V_{o,a}>0\}
\right|
\le m
\right\}.
\]

Then round-robin through the currently least-covered occupations:

\[
T_4
=
\arg\max_{\substack{T\subseteq A_{\mathrm{niche}}\setminus S_3\\|T|=B_4}}
\text{niche occupation coverage}(S_3\cup T).
\]

This prevents occupationally specialized actions from losing to broadly reusable ones.

## k5: Category and mechanics fill

The final tier fills structural holes left after all value- and domain-driven tiers.

For robotics, “category” should include frozen high-level families such as:

- Robot capability families: locomotion, bimanual manipulation, dexterity, force control, visual/tactile sensing, tool use.
- Physics families: rigid contact, articulated mechanisms, compliance, cloth, granular matter, fluids, adhesion, fracture/cutting, thermal effects, aerodynamics, biological deformation.
- Tool/object/work-system families where appropriate.

Let \(G\) be the set of these families, and \(q_g(S)\) indicate whether portfolio \(S\) adequately covers family \(g\). Then k5 can maximize:

\[
T_5
=
\arg\max_{|T|=B_5}
\sum_{g\in G}
\omega_g
\left[
q_g(S_4\cup T)-q_g(S_4)
\right],
\]

with remaining economic coverage used as a tie-breaker.

## Complete pipeline

The result becomes:

```text
k1   economic core
 ↓
k2.1 strategic-domain coverage
 ↓
k2.2 STEM/research coverage
 ↓
k3   SOC-major breadth
 ↓
k4   niche occupation-specific coverage
 ↓
k5   capability/mechanics/category fill
```

Every action is selected once, but can improve every metric. Its tier label records why it entered the portfolio, not the only area it covers.

## Three important implementation rules

### 1. Optimize each tier as a batch

Capability coverage contains complementarities. One action may supply force control while another supplies deformable contact; neither alone covers a valuable target, but together they do.

Therefore marginal coverage is not reliably submodular, and purely one-at-a-time greedy selection can miss strong bundles. Use a MILP for each tier where practical; round-robin tiers can still process groups sequentially while optimizing each group’s sub-batch.

### 2. Condition every tier on earlier coverage

Do not rerank candidates from scratch in each tier. k2 must see everything covered by k1, k3 must see k1+k2, and so on. Otherwise the portfolio will spend slots repeatedly acquiring the same capability bundles.

### 3. Freeze budgets before inspecting results

If the total portfolio remains 100, directly copying the paper’s 500-slot budgets is impossible. A proportional illustrative allocation would be:

| Tier | Illustrative slots |
|---|---:|
| k1 | 20 |
| k2.1 | 20 |
| k2.2 | 20 |
| k3 | 23 |
| k4 | 9 |
| k5 | 8 |
| Total | 100 |

Those numbers should be treated as a policy choice, not optimized after seeing which allocation produces the nicest result.

## Relationship to the current maximin portfolio

The present eight-view maximin solution should become a baseline:

- **Current baseline:** one global optimization maximizing the weakest view.
- **New method:** explicit Gym-Anything tiers with sequential marginal capability coverage.

Then compare:

- Economic coverage.
- Weakest-view coverage.
- Mean-view coverage.
- Actions fully covered.
- SOC/occupation breadth.
- Strategic and STEM coverage.
- Niche occupations represented.
- Robot and physics families covered.
- Redundancy between selected action groups.

The global maximin solution may achieve slightly better numerical balance. The tiered solution will likely be easier to explain, audit, and intentionally shape.

So yes: this is the right plan. It is the original Gym-Anything selection philosophy applied to a capability-dominance graph over physical action groups.
