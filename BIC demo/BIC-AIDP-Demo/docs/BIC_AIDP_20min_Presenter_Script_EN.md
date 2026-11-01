# BIC AIDP demonstration script

## Complete English script for 20 minutes

Approx. 1,727 spoken words. Slides, demo, questions, clicks and pauses are included. Read SAY and ASK aloud; DO and CHECK are presenter cues. Pace: about 115 words per minute.

## 00:00–02:00  The business situation

Screen: Slides 1 and 2

**DO**

Start the timer on slide 1. Use slide 2 at approximately 00:45. Speak as the BIC customer service and supply chain manager. Do not open with a list of numbers.

**SAY**

Good morning, and thank you for joining. Over the next twenty minutes, I will show how BIC can move from a supply risk to a decision that a manager can review and act on.

Our user is responsible for customer service and supply chain at BIC France. BIC supplies the distributors. The challenge is to keep customer commitments while protecting margin and the stock needed by other accounts.

We will follow that person's working day: understand where attention is needed, investigate an account, compare solutions and prepare a decision.

**DO**

Move to slide 2.

**SAY**

Carrefour is preparing for the back-to-school period. BIC has committed to a delivery date, but a transport delay pushes an inbound receipt beyond that date.

Moving stock could help, but that stock may support another customer. Accelerating supply costs money. Changing the delivery plan requires a conversation with the distributor. The manager needs to know what BIC can still commit to.

Today, the source data is in Object Storage. JDE is the future integration context; it is not connected in this demonstration.

Let me show how AIDP supports this decision.

**CHECK**

Business roles and scope are clear. No numerical KPI needs to be read on slide 2. Move on by 02:00.

## 02:00–03:15  The AIDP decision chain

Screen: Slides 3 and 4

**DO**

On slide 3, follow the picture from left to right. Move to slide 4 for the last paragraph.

**SAY**

The chain starts with orders, stock allocations, planned receipts, transport events, budgets and policies in Object Storage.

AIDP notebooks organise the data through Bronze, Silver and Gold: preserve the source, check its quality, then publish consistent facts for analysis. Machine learning provides a demand forecast and a service-risk probability.

The numerical tools calculate dated shortages, transfer quantities, costs and policy results. The agent retrieves the evidence needed for the question and explains the trade-offs.

That distinction matters: a high score does not explain a transport delay. The explanation comes from dated operational evidence. The agent brings that evidence into the decision, and the human remains responsible for approving the action.

Let us start with the national picture.

**CHECK**

Do not imply that the model establishes causes, that the agent invents quantities, or that this is an autonomous approval process. Switch to the English application by 03:15.

## 03:15–05:00  Find the exceptions across France

Screen: National overview

**DO**

Open the English application at http://127.0.0.1:8766/. Start on National overview with no selected account or regional filter. Use the floating agent panel.

**SAY**

This is the national portfolio. The budget is the commercial target. The sales forecast is expected demand valued at the net selling price. Gross margin exposure tells us where uncovered demand may put margin at risk. It is an exposure, not a loss already recorded.

Rather than read every tile, I will ask where we should focus.

**ASK**

Which regions and accounts need attention today, and why?

**DO**

Submit the question and allow the response to finish. Point to the accounts and dated evidence it returns. Close the panel, select Île-de-France, click a day on the curve, then select All France.

**SAY**

The important distinction is between an order still uncovered at its promise date and a temporary gap earlier in the week. Both deserve attention. The list should not be restricted to the highest probability scores.

Selecting a region filters the curve below. A comfortable national total can hide a local problem: the right product still needs to be available for the right account, on the right date.

Let us investigate Carrefour.

**CHECK**

Expected dated exceptions: Carrefour, E.Leclerc, Monoprix and METRO. The region filter changes the curve; it does not select an account. If the answer omits an exception, use the dated facts on screen rather than claiming it found everything.

## 05:00–07:00  Understand the Carrefour shortfall

Screen: Distributor accounts → Carrefour Hauts-de-France → Details

**DO**

Open Carrefour. Keep the initial scenario: Demand uplift 35%, Total inbound delay 4 days. Point to the product, account name, dated transport event and quantity tiles. Click 30 August and then 31 August on the curve.

**SAY**

We are now looking at Carrefour in Hauts-de-France, for BIC Cristal Original. The account and product stay visible so we know exactly which commitment we are discussing.

The firm order is ninety-seven thousand, three hundred and fifty units. Stock already allocated and receipts expected on time cover eighty-two thousand, two hundred and fifty. That leaves fifteen thousand, one hundred firm units uncovered at the promised date.

The operational explanation is visible here: the main receipt has moved from the twenty-eighth of August to the first of September, after the promise date. The incident record explains the gap; the probability score is a separate statistical signal.

On the curve, green is cumulative supply available by each date. Yellow is cumulative forecast demand. When yellow rises above green, the forecast has a dated coverage gap.

At the end of the week, the forecast gap is twenty-one thousand, two hundred and seventy-five units. It is larger than the firm-order deficit because forecast demand also anticipates demand beyond existing orders. We do not add the forecast to the firm order, and we do not add the cumulative gaps across days.

Now we can ask which action makes sense.

**CHECK**

Firm order 97,350; allocated 64,100; timely future receipts 18,150; firm deficit 15,100. Main receipt 26,500 moves to 1 September. Forecast 103,525; peak gap 21,275. On 30 August: 84,432 demand versus 82,250 supply, gap 2,182. These are different measures, not contradictory totals.

## 07:00–09:00  Ask the agent to compare remedies

Screen: Carrefour account workspace and solution details

**ASK**

Compare the solutions for this scenario. Explain which policies pass or block each option.

**DO**

Submit the question. Keep the curves above the response. After the solution tiles appear, select Internal BIC transfer. Point to donor and receiver, then open STK-01, FIN-01 and AUT-01.

**SAY**

The solutions appear in response to our question. We can inspect the tools used and then explore the options.

For the transfer, the donor is BIC Centre Warehouse and the receiver is Warehouse BIC North. Available stock excludes reservations for other customers and protected safety stock.

The proposed move is fourteen thousand, four hundred units, in the required shipping multiples, with an estimated freight cost of two hundred and eighty-seven euros. Seven hundred firm units remain uncovered. That remainder needs a decision as well.

The policy results tell us what is acceptable and what still needs review. We can open the actual rule rather than rely on a green label. Passing the margin check does not reserve stock or confirm a transport slot.

This is the agent's contribution: connecting the question to the operational evidence, explaining feasible alternatives and making the unresolved conditions visible. We will return to this proposal for human validation.

**CHECK**

Transfer 14,400; estimated arrival 26 August; freight €287; margin after freight 25.6%, above the 25% floor. Mobilizable stock 25,650 after reservations and safety. Firm remainder 700. Human approval is still required. Do not describe all forecast demand as secured.

## 09:00–11:00  Expose the temporary gap at Monoprix

Screen: Monoprix Île-de-France account workspace

**DO**

Open Monoprix from Distributor accounts. Initial scenario: Demand uplift 10%, Total inbound delay 3 days. Show 26 and 27 August on the curve, then ask the combined question below.

**SAY**

Monoprix illustrates why the final total is not enough. There is no firm-order deficit at the end of the week, but two earlier days are uncovered. A delayed factory packing operation moves the receipt from the twenty-fifth to the twenty-eighth of August. Later recovery does not remove the earlier exposure.

**ASK**

Why does Monoprix need action when the final deficit is zero? Compare ways to prevent the temporary gap and check the margin policy.

**DO**

After the response, select the transfer and click FIN-01. Then select Transfer case to manager. This is a local workflow demonstration; it sends no message.

**SAY**

There is enough donor stock, but the proposed eighteen-thousand-unit transfer fails the margin rule. After freight, the option margin is twenty point nine percent; the required minimum is twenty-five percent.

An explanation cannot override that control. I can transfer the case for manager review, with Finance involved. Escalation does not approve an exception.

This is a useful outcome: the agent has helped us identify an operational need and understand why the obvious remedy is not yet acceptable.

**CHECK**

Receipt 50,870 on 28 August; peak temporary gap 17,155 on 26–27 August; final firm deficit zero. Transfer 18,000; freight €617; 20.9% margin; FIN-01 BLOCKED. Mobilizable donor stock 33,850. Escalation remains distinct from approval.

## 11:00–12:45  Change the scenario and challenge the answer

Screen: Monoprix simulator beside the coverage curve

**DO**

Keep uplift at 10%. Change Total inbound delay from 3 to 4 days and click Apply scenario. Observe the changed receipt date and gap. The previous solutions should disappear.

**SAY**

Let us test one more day of delay. The slider is the total delay, so I move it from three days to four. The curve changes, and the previous comparison must no longer be used.

**ASK**

Recompare the solutions using the four-day delay now shown in the chart. What changes?

**DO**

Select the updated transfer. Check the figures against the new curve and open FIN-01 again.

**SAY**

The peak need increases to thirty thousand, one hundred and ninety units. The proposed transfer rounds up to thirty-one thousand, two hundred, using the shipping multiple.

The quoted freight remains the same in this scenario. Spreading it over more units brings the option margin to twenty-five point six percent, so that specific check now passes.

This does not mean that a bigger delay is good news. We still need transport confirmation and commercial review of a quantity driven by the forecast. What matters is that the answer and the policy checks now refer to the scenario we are actually discussing.

**CHECK**

Receipt moves to 29 August. Gap 30,190; transfer 31,200; freight €617; margin 25.6%. Do not combine the old and new proposals. The simulation is a hypothesis, not a newly observed transport event.

## 12:45–15:30  Show what is running in AIDP

Screen: Prepared Object Storage and AIDP tabs

**DO**

Spend about 25 seconds on Object Storage, 45 on notebooks and Gold, 35 on MLOps, and 45 on an existing agent trace. Use tabs prepared before the session; do not start training or a cluster now.

**SAY**

Let me show the platform behind that interaction. These source files are in Object Storage: accounts, orders, supply events, budgets, policies and historical observations. There is no live extraction from JDE in this demonstration.

The four notebooks ingest the sources, check data quality, train and track the models, then publish the baseline Gold facts. Here is the calculation call for the Monoprix scenario we just used. Its parameters and dates correspond to the application.

The agent calculates alternatives during the conversation by calling Python tools. It chooses the candidates to evaluate, checks the returned costs and policy results, and recommends an option for human review. The tools use a versioned copy of the Object Storage inputs and trained model weights. The local simulator uses the same numerical logic.

In MLOps, we can inspect the model run, parameters and evaluation. The demand model predicts weekly units. A daily planning profile distributes those units across the week. The risk model estimates a service-risk probability. These are distinct outputs.

The metrics shown here come from the demonstration dataset. Before using this operationally, we would validate them on BIC history, using an agreed definition of service failure.

Finally, this trace shows which tools the agent actually called. SQL tools retrieve baseline portfolio facts. Custom Code tools calculate the current scenario and candidate remedies; policy retrieval supplies the relevant rules. The agent selects evidence for the question and explains the trade-offs.

The controls remain explicit: numerical code evaluates the rules, the response is tied to the current scenario, and a person reviews the proposal.

**CHECK**

Object Storage prefix: Demo_BIC/bic-retail-v1/raw/. Workspace: /Workspace/BICDemo/notebooks. Runtime tools: calculate_account_scenario and evaluate_transfer, OPP-007 / 10 / 4. Agent: BIC_Retail_Service_Copilot. Show only tools actually present in the trace. Do not describe a previously recorded trace as a new invocation.

## 15:30–17:30  Prepare the human decision

Screen: Carrefour transfer and Decision follow-up

**DO**

Return to Carrefour at 35% uplift and 4 total delay days. Ask the comparison prompt again because opening an account clears its previous answer. Select the transfer, then Prepare for human validation.

**ASK**

Compare the solutions for this scenario. Explain which policies pass or block each option.

**SAY**

We now return to the Carrefour proposal and prepare the decision for review. The record captures the account, scenario, quantity, cost and policy results. The seven-hundred-unit remainder stays visible.

For this demonstration, I am playing the Operations and Account manager reviewer roles. In production, authenticated identities and a managed workflow would enforce those responsibilities.

**DO**

Check I have reviewed quantities, dates, freight and policy results. Select Confirm as Operations. Check the review box again, then Confirm as Account manager. After both approvals, select Export target integration payload and Download JSON. Open Decision follow-up if time permits.

**SAY**

Both required reviewers must confirm before the export is available. If a reviewer is unavailable, the case can be escalated; that does not remove the other controls.

The result is a reviewed integration payload, ready for a future hand-off. It has not been transmitted to JDE. Before execution, the operational process would recheck stock, transport and authorization.

We have moved from a signal to a documented proposal with conditions and named review responsibilities.

**CHECK**

Frozen proposal: transfer 14,400, freight €287, firm remainder 700. Required roles: Operations and Account manager. Final state EXPORT READY means prepared, not sent. The local validation flow is not production identity or segregation-of-duties enforcement.

## 17:30–20:00  Explain the value and close

Screen: Slides 5 and 6

**DO**

Use slide 5 until about 18:15, then slide 6. Aim to begin the final paragraph by 19:00. The last 30–45 seconds are a buffer for earlier latency or a brief audience response.

**SAY**

The value for BIC is the quality and speed of this decision process. We would measure time spent investigating, service gaps addressed, incremental freight, margin discipline and the completeness of the decision record.

The margin exposure on one screen is not an annual return on investment. A pilot should measure the benefit across the real volume of decisions, against today's way of working.

In a future BIC architecture, JDE could remain the operational system of record. AIDP would bring together operational facts, forecasts and policies to support the investigation and preparation of decisions.

We would agree the data definitions with the JDE team, validate the models on BIC history, confirm the policies and implement a controlled hand-off with acknowledgements. The approval flow shown today is a demonstration of those responsibilities; it is not a production JDE workflow already installed.

What we have seen is a practical working sequence. The manager asks where to focus, understands what happened, challenges a remedy, tests a new assumption and submits a proposal for review. The agent makes that investigation interactive, while the evidence and controls remain visible.

For a pilot, which outcome would matter most to you: faster investigation, better service coverage, or stronger control of logistics cost and margin?

**DO**

Pause for a brief reaction if time remains. Finish by 20:00. If a longer discussion starts, offer to take it immediately after the timed demonstration.

**CHECK**

No invented ROI or promise that the demonstrated workflow is already a configured JDE integration. Keep the distinction between the current Object Storage demo and the future operational architecture.

## Preparation and timing control

Presenter reference only. Outside the spoken script.

**Prepare the tabs.** Open the English deck, the application on port 8766, the Object Storage prefix, the notebook folder, the current scenario calculation, a completed MLOps run and a verified agent trace. Use the current deployment status document for setup. No cluster start or training belongs in the timed route.

**Check the mode.** The application should show AIDP agent mode for the live agent demonstration. Verify connectivity before presenting. A locally generated rehearsal response must be identified as rehearsal, never as a live AIDP response.

**Reset the starting state.** Use Reset view. Start with All France and no selected account. Carrefour begins at 35% demand uplift and 4 total delay days; Monoprix begins at 10% and 3 days. Changing Monoprix to 4 days is the one deliberate simulation in the main route.

**Keep the prompts ready.** The main route has five submissions: national exceptions; Carrefour comparison; Monoprix gap and comparison; Monoprix re-comparison; Carrefour comparison again for approval. Copy the exact ASK text from the script, not the CHECK notes.

**When an answer takes time.** After about 25 seconds, continue by showing the already visible curve and policy context. If the service fails, say: “The live agent is unavailable. I will use the clearly labelled rehearsal mode to explain the remaining decision flow.” Do not silently switch modes.

**If one minute behind.** Shorten the platform tour to the current scenario calculation and the actual tool trace. Keep the Monoprix margin block, the changed scenario and the human decision. Do not add Leclerc or METRO to the timed route.

**If two minutes behind.** Use the same 60-second platform shortcut and omit the JSON download and audit expansion. Still show the required reviewers and explain that export is prepared, not sent. Shorten the value close to the final paragraph.

**If you finish early.** Use the closing pilot question and allow a short response. Reserve questions below are for discussion after the 20-minute route, not mandatory extra content.

## Reserve answers for discussion

Outside the 20 minute route.

### What does the agent add to the dashboard

The dashboard shows facts and calculated gaps. The agent responds to the user's question, retrieves relevant evidence and policies, compares the options and explains what still requires a decision. The numerical tools, rather than the language model, establish quantities and rule status.

### Why does zero final deficit still require attention

A receipt can restore coverage at the end of the week after demand has exceeded available supply on earlier dates. We inspect the trajectory. A forecast gap calls for investigation and potentially preventive action; it is not automatically a missed firm customer commitment.

### Why is the forecast gap larger than the firm deficit

The firm order is an existing commitment. The forecast also anticipates demand beyond that order, and the forecast is floored at firm demand. We do not add the two quantities. A preventive move based on the forecast requires commercial review.

### Why does the Monoprix margin improve with a larger transfer

In this scenario, the same quoted freight cost is spread over more units. That changes the option margin calculation. It does not make a longer delay desirable or establish that all the additional quantity will be sold.

### How can I demonstrate that an alternative is not prerecorded

At Carrefour, with 35 percent uplift and four days of delay, ask: Evaluate an internal transfer of exactly 13,200 units. Keep this quantity. The tool calculates a 24.986 percent margin, below the 25 percent floor, and a 1,900-unit firm remainder. Show the actual evaluate_transfer call and calculation time. This differs from the default 14,400-unit candidate.

### Can the agent approve or send a transaction to JDE

No. Its tools retrieve and analyse. The application demonstrates human review and exports a proposed integration contract. A production implementation would need authenticated reviewers, durable workflow, operational rechecks and a controlled JDE interface.

### Are these model metrics BIC production performance

No. They demonstrate the evaluation workflow on the demonstration dataset. The weekly forecast WAPE is 10.25%, compared with 22.53% for the simple baseline; the risk ROC-AUC is 0.905. BIC history, service labels and a chronological backtest would be required to establish production performance.

### Are alternatives calculated during the conversation

For account questions, yes: the agent calls a Python tool to calculate the current scenario. Remedies are also evaluated on demand, and the agent chooses its recommendation from those results. Source inputs, model weights and allowed action families are prepared in advance; alternative results and recommendations are not. Final approval remains human.

