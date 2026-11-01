# BIC Retail Studio — guide présentateur
## 25 minutes : présentation en anglais et démonstration AIDP

**Votre rôle pendant la démo :** responsable Customer Service & Supply Chain de BIC France. BIC est le fournisseur ; Carrefour, E.Leclerc, Monoprix et METRO sont les distributeurs. Les comptes sont des périmètres régionaux de scénario, pas une représentation des organisations contractuelles réelles des enseignes.

**Le message central :** la valeur de l’agent est la préparation d’une décision opérationnelle justifiée. Il rapproche une question, des faits datés et les politiques ; il compare les options et expose leurs limites. Les modèles prévoient et scorent. Les outils calculent. La personne décide.

**Périmètre à annoncer une seule fois :** les données de démonstration sont dans Object Storage. Aucun accès à JDE, aucune réservation physique, aucun message à un distributeur et aucune transmission à JDE ne sont exécutés. JDE intervient uniquement dans le discours sur l’architecture cible. La validation est une répétition du futur processus, pas un système d’autorisation de production.

> “Today, the data is in Object Storage. We are demonstrating the decision journey. JDE is the future operational integration context, not a connected system in this demonstration.”

## Préparation avant la réunion

### Les fichiers à avoir ouverts

1. `presentation/BIC_AIDP_25min_EN.pptx` : six diapositives principales ; les deux annexes sont masquées en mode diaporama. Les notes sont en anglais.
2. L’application anglaise : `http://127.0.0.1:8766/`. La version française historique reste séparée sur son port habituel.
3. Le workspace AIDP : dossier `/Workspace/BICDemo`, catalogues `bronze.bic_bronze`, `silver.bic_silver`, `gold.bic_gold`.
4. L’expérience MLOps `BIC_Retail_Service_Risk` et le dernier run terminé.
5. L’agent `BIC_Retail_Service_Copilot`, son Playground et la trace d’une réponse vérifiée.
6. Le bucket `AIDP_DATA`, namespace `frn9volod3kr`, préfixe `Demo_BIC/bic-retail-v1/`.

Consulter `DEPLOYMENT_STATUS.md` avant de présenter : il donne les identifiants déployés, les vérifications effectuées et les limites du périmètre. Ne pas appeler « live AIDP » une session de répétition locale.

### Démarrage local

Depuis la racine du package :

```bash
# Si la CLI OCI n'est pas dans le PATH :
export OCI_CLI="$HOME/.local/bin/oci"
export OCI_CONFIG_PROFILE=DEFAULT
python3 scripts/sync_cloud_exports.py
bash scripts/start_aidp.sh
```

Le script utilise l’agent BIC déjà déployé et vérifié. La page indique **AIDP agent mode**. Pour une répétition sans appel cloud, lancer explicitement `BIC_MODE=rehearsal python3 runtime/server.py --port 8766`. Ne lancer qu’un seul serveur sur ce port.

Ne jamais réutiliser l’endpoint SPORT ou RetailNova. La CLI OCI doit être authentifiée. En mode AIDP, une erreur de l’agent reste une erreur : l’application ne remplace pas silencieusement la réponse par un scénario local.

### Contrôle à J−1 puis dix minutes avant

- Vérifier que le cluster Spark et l’AI Compute de l’agent sont disponibles. Ils sont distincts.
- Vérifier les données Gold, le run MLOps et la version de politiques 1.2. Les exports locaux et cloud doivent provenir du même snapshot.
- Tester une question globale, une question Carrefour et une comparaison Monoprix après changement du délai. Vérifier que le hash du scénario correspond.
- Vérifier que les photographies de Cristal et 4 Colours sont visibles ; elles sont locales. Les autres photographies de gamme peuvent dépendre de leur hébergeur.
- Cliquer sur **Reset view** : aucun compte sélectionné sur l’accueil, aucun filtre régional conservé. Ce bouton ne supprime pas les décisions enregistrées.
- Préparer les onglets AIDP avant la réunion. Ne pas entraîner les modèles ni démarrer un cluster à froid pendant les 25 minutes.
- Garder les captures et les chiffres de ce guide comme support de secours. Si un service est indisponible, le dire et montrer le parcours en mode répétition explicitement identifié.

## Conducteur chronométré

| Temps | Écran | But |
|---|---|---|
| 00:00–01:30 | Slide 1 | Installer le rôle métier et le problème |
| 01:30–03:00 | Slide 2 | Installer la situation métier et les arbitrages |
| 03:00–05:00 | Slide 3 | Présenter les briques AIDP et Object Storage |
| 05:00–06:00 | Slide 4 | Distinguer modèle, outils, agent et humain |
| 06:00–06:30 | Transition | Passer à l’application, rappeler le périmètre |
| 06:30–08:30 | National overview | Passer des KPI aux régions et comptes concernés |
| 08:30–10:30 | Carrefour | Lire les quantités et la cause datée |
| 10:30–12:30 | Carrefour + agent | Comparer les solutions et les politiques |
| 12:30–16:30 | Monoprix | Montrer un risque temporaire, un blocage, puis une simulation |
| 16:30–19:30 | AIDP | Montrer données, notebooks, MLOps et outils de l’agent |
| 19:30–21:30 | Validation | Faire valider un dossier et exporter le contrat cible |
| 21:30–22:30 | Slide 5 | Expliquer les mesures de valeur |
| 22:30–23:30 | Slide 6 | Relier la démonstration au contexte JDE BIC |
| 23:30–25:00 | Marge | Une question client ou absorber la latence |

Total : **8 minutes de slides + 15 minutes de démo + 2 minutes de transition/marge**. Les annexes ne s’ajoutent pas au parcours principal.

## 00:00–06:00 — présentation

### Slide 1 — Protect the promise. Make the next decision.

Ne pas commencer par une liste de fonctionnalités techniques. Installer une matinée de travail concrète : la rentrée approche, un transport est décalé, plusieurs comptes ont des signaux à examiner, le responsable doit arbitrer sans compromettre les autres clients ni la marge.

> “Imagine you are responsible for customer service and supply chain at BIC France. A major distributor has an upcoming commitment. Demand is moving, a receipt is late, and moving stock has a cost. Your question is not just ‘What is the risk?’ It is ‘What can we do, by when, under which rules, and who needs to approve it?’”

> “The demonstration follows that decision from the national picture to one account, then to a reviewed action.”

### Slide 2 — Carrefour’s back-to-school order needs a decision

**Intention : installer l’histoire métier avant les chiffres.** Vous êtes le responsable Customer Service & Supply Chain de BIC. Carrefour attend sa commande pour la rentrée ; un retard transport remet la promesse en question. La personne doit arbitrer entre service client, marge, disponibilité pour les autres distributeurs et règles d’entreprise. Ne pas lire de KPI ni détailler le calcul du déficit sur cette slide.

> “You are BIC’s Customer Service and Supply Chain Manager. Carrefour is preparing for the back-to-school period and expects the order BIC has promised. Then a transport delay pushes a key inbound receipt past that delivery date. You need to decide what BIC can still commit to.”

> “Moving stock might protect Carrefour, but that stock may already be needed by another customer. Accelerating a receipt adds cost and needs confirmation. Changing the delivery plan requires the distributor’s agreement. You need a recovery plan that protects service and margin and respects the company’s rules.”

> “The demo follows that decision: understand the issue, compare feasible options, check the evidence and policies, and submit a proposal for human review.”

**Transition vers la slide 3 :**

> “Let us first see how AIDP brings the information and the decision process together.”

**Réserve, uniquement si l’on demande les chiffres :** 97 350 stylos commandés − 64 100 déjà alloués − 18 150 attendus à temps = **15 100 unités de commande ferme non couvertes au 31 août**. La réception principale de 26 500 unités passe du 28 août au 1er septembre. Les 26 500 unités retardées et le déficit final mesurent donc deux choses différentes. Les 103 525 unités de demande prévue incluent les commandes fermes ; ne pas les additionner. Le pic de demande non couvert est de 21 275 unités. Le score de 54,7 % est une probabilité, pas un pourcentage d’unités manquantes. Ces détails seront montrés pendant la démo.

### Slide 3 — One continuous chain to a human decision.

Reprendre le mécanisme vu dans SPORT, avec les sources B2B.

> “We start with files in Object Storage: accounts, firm orders, allocated inventory, planned receipts, dated incidents, budget and historical observations. Four notebooks ingest, check, train and publish the data. The agent queries the published facts and the policy evidence. The application presents the decision for human review.”

> “The same scenario and policy version are used from the question to the decision record.”

Préciser que Spark réalise les traitements de données et prépare les modèles et faits de référence. L’AI Compute exécute le flow agent et ses outils Python de calcul à la demande. MLOps conserve les paramètres, métriques et artefacts. La recherche de politiques apporte des sources ; les règles numériques restent évaluées par du code déterministe.

### Slide 4 — The agent makes the investigation interactive.

> “ML forecasts demand and estimates risk. Tools calculate quantities, dates and policy results. The agent chooses the relevant evidence for the question, explains the operational cause and compares the trade-offs. A human remains responsible for the decision.”

> “The options are not displayed as a permanent dashboard answer. They appear when the user asks how to resolve the situation.”

## 06:30–08:30 — partir du portefeuille national

**Manipulation :** ouvrir **National overview**, sans compte sélectionné. Montrer les quatre KPI financiers, puis le nombre de comptes et d’exceptions. Tous les montants sont en euros HT sur la semaine du 25 au 31 août.

| KPI de départ | Valeur attendue | Ce qu’il faut expliquer |
|---|---:|---|
| Revenue budget | €861,378 | Objectif budgété pour le même périmètre et la même semaine |
| Sales forecast · net revenue | €823,951 | Quantités prévues × prix net ; ce n’est pas du CA déjà facturé |
| Forecast versus revenue budget | −€37,427 | Écart de demande valorisée, avant toute déduction liée au service |
| Gross margin exposed at peak | environ €8,836 | Somme par compte du pic non couvert × prix × taux de marge ; exposition, pas perte certaine |
| Dated coverage exceptions | 4 | Carrefour, Leclerc, Monoprix et METRO ; pas un filtre sur le seul score |
| Firm units uncovered at promise | 15,100 | Déficit des engagements fermes au 31 août |
| Forecast gross margin | environ €252,279 | Marge de la demande prévue avant surcoûts et pertes de service |

> “Revenue, gross margin and units answer different questions. We keep them separate. The margin exposure is not a booked loss, and we do not subtract it twice from the forecast.”

**Question à saisir dans le bouton flottant :**

> “Which regions and accounts need attention today, and why?”

**Réponse à chercher :** les quatre exceptions, avec la distinction déficit final / trou temporaire ; notamment Leclerc doit remonter malgré un score d’environ 37,9 %. Ne pas exiger une formulation mot pour mot d’un LLM ; vérifier les faits.

**Manipulation :** fermer le panneau si nécessaire, sélectionner **Île-de-France** sur la carte ou dans la liste. La courbe en dessous doit se filtrer sur Leclerc et Monoprix. Cliquer une date pour lire demande quotidienne, réceptions et cumul. Revenir à **All France** avant d’aller à Carrefour.

> “A national total may look comfortable while one regional account has a dated shortage. The map changes the scope of the curve; it does not silently select a customer.”

## 08:30–10:30 — Carrefour : lire le problème avant d’agir

**Manipulation :** **Distributor accounts → Carrefour / Hauts-de-France → Details**. Montrer la photographie du produit, le nom du compte et l’événement transport. Descendre jusqu’aux courbes.

**Question :**

> “What exactly is uncovered for Carrefour, and which event explains it?”

**Attendu :** réception de 26 500 unités décalée après le 31 août ; 15 100 unités fermes manquent à la date promise ; la demande prévue dépasse les ressources pendant deux jours. Ce n’est ni une cause inventée par le modèle, ni un problème supposé en magasin.

Cliquer le **30 August** : demande cumulée **84 432**, disponibilité cumulée **82 250**, manque **2 182**. Cliquer le **31 August** : demande cumulée **103 525**, disponibilité **82 250**, manque **21 275**. Ne pas additionner 2 182 et 21 275 : les deux valeurs sont des écarts cumulés.

> “The green line is cumulative supply available by that date. The yellow line is cumulative forecast demand. When yellow is above green, we have a dated coverage need. A later receipt does not undo the earlier disruption.”

## 10:30–12:30 — rendre le travail de l’agent visible

**Question :**

> “Compare the solutions for this scenario. Explain which policies pass or block each option.”

**Manipulation :** attendre la réponse ; les courbes restent au-dessus. Les tuiles de solutions apparaissent après la question. Cliquer **Internal BIC transfer**, puis **STK-01**, **FIN-01**, **AUT-01**.

**Chiffres attendus au scénario initial :**

- Transfert proposé : **14 400 unités**, arrivée **26 August**, transport **€287**.
- Entrepôt donneur **BIC Centre Warehouse**, receveur **Warehouse BIC North**.
- Stock physique **74 850** − réservations **36 900** − sécurité **12 300** = **25 650 mobilisables**.
- Multiple d’expédition : **1 200**. La commande ferme présente un manque de 15 100 ; on retient 12 multiples, soit 14 400. Le reliquat ferme est **700** ; il ne faut pas le masquer.
- Marge de l’option après transport : **25,6 %**, au-dessus du plancher **25 %**.
- **AUT-01** exige une validation humaine. **CLI-01** impose une revue commerciale pour le reliquat.
- L’accélération usine est conditionnelle : capacité/transport non confirmés. La livraison fractionnée nécessite un accord client et un coût ; elle ne crée pas de stock.

> “The agent is not just saying ‘transfer stock’. It explains which warehouse can give, which warehouse receives, how much remains uncovered, what the move costs, and which policy still requires a person.”

Ne pas annoncer « rupture résolue » : 700 unités fermes restent à traiter et la demande prévue peut avoir un besoin supplémentaire.

## 12:30–16:30 — Monoprix : le cas qui rend la valeur visible

### Première situation : déficit final nul, problème réel pendant deux jours

**Manipulation :** **Distributor accounts → Monoprix / Île-de-France → Details**. Le scénario initial est **10 % de hausse**, **3 jours de retard total**.

**Question :**

> “There is no final order deficit. Do we still need to act, and why?”

**Attendu :** conditionnement usine retardé, réception de **50 870 unités** du **25** au **28 August**. Couverture insuffisante le **26** et le **27** ; pic **17 155 unités**. Rattrapage le **28**. Au 31, le déficit de commande ferme est nul. L’action relève de la prévention du trou de couverture, pas de l’invention d’une nouvelle promesse client.

**Question suivante :**

> “Compare ways to prevent the temporary gap. Can we use the donor warehouse without breaking our margin policy?”

Cliquer le transfert : **18 000 unités**, arrivée **26 August**, **€617** de transport, marge après transport **20,9 %**. **FIN-01 est bloquante**. Montrer la règle cliquable et son plancher 25 %. Le stock mobilisable est **33 850**, mais disponibilité ne veut pas dire acceptabilité économique.

> “This is where the agent helps with the trade-off. There is enough stock, but the proposed move fails the margin rule. A persuasive explanation cannot override that control.”

Cliquer **Transfer case to manager**. La demande est orientée vers le responsable supply chain, avec Finance consultée pour FIN-01. **L’escalade ne vaut pas approbation de dérogation.** Aucun stock n’est réservé.

### Deuxième situation : la simulation change les chiffres de la comparaison

**Manipulation :** rester sur Monoprix. Dans le simulateur près de la courbe, passer le retard total de **3 à 4 jours**, puis **Apply scenario**. Les anciennes solutions disparaissent. Ne pas dire « un retard supplémentaire de quatre jours » : le réglage signifie quatre jours au total.

**Question :**

> “Recompare the solutions using the four-day delay now shown in the chart. What changes?”

**Attendu :** réception le **29 August**, pic de besoin **30 190 unités**, transfert préventif arrondi à **31 200**, toujours dans les **33 850 mobilisables**, coût **€617**, marge après transport **25,6 %**. Les statuts de politiques sont recalculés. L’option passe à une revue humaine au lieu d’un blocage FIN-01.

> “The larger move does not automatically make the business better. It spreads the same quoted freight over more units, so this specific margin check now passes. We still need transport confirmation and a commercial review of the forecast-driven quantity.”

Montrer que les valeurs de la réponse correspondent au scénario courant et non au scénario précédent. Ne pas fusionner les quantités des deux propositions. L’hypothèse utilisateur n’établit pas une nouvelle cause d’incident.

## 16:30–19:30 — ouvrir AIDP : la mécanique de la démo

### 30 secondes — Object Storage

Montrer le préfixe `Demo_BIC/bic-retail-v1/raw/` et les fichiers : accounts, supply, budget, policies, historical_snapshots. Le jeu comporte **26 comptes** et **8 064 observations historiques**.

> “These are the demo sources. There is no JDE extraction running behind this screen.”

### 60 secondes — notebooks et tables

Dans `/Workspace/BICDemo/notebooks`, montrer les quatre notebooks sans relancer les traitements :

1. **01_bronze_ingest** : lecture `oci://`, conservation de la provenance.
2. **02_silver_quality_features** : unicité, raccordement des comptes, calculs de stock, temporalité des labels.
3. **03_ml_training_mlops** : entraînement et suivi des modèles.
4. **04_gold_scenarios_publish** : faits de référence du portefeuille, politiques, métriques et exports. Les alternatives ne sont pas préenregistrées.

Montrer l’appel `calculate_account_scenario` pour OPP-007 / 10 / 4, puis `evaluate_transfer` dans la trace. Les outils recalculent les dates, quantités, coûts et règles pendant la question. Les entrées et poids du modèle sont un instantané versionné issu d’Object Storage, embarqué dans le package ; ce ne sont pas des réponses stockées.

> “The notebooks prepare facts and numerical tools. They do not pre-author the answer to every business question.”

### 45 secondes — modèles

Montrer le run MLOps vérifié et les métriques. Si le run cloud n’est pas disponible, utiliser l’onglet **Data & models** en disant explicitement qu’il s’agit des métriques de répétition locale.

- Risque : régression logistique, ROC-AUC **0,905**, Brier **0,119**.
- Demande hebdomadaire : régression log-linéaire, WAPE **10,25 %**, contre **22,53 %** pour la référence simple.
- Split chronologique : **5 760 / 1 152 / 1 152** observations ; seuil choisi sur la validation.

> “These measurements validate the demonstration workflow on synthetic outcomes. Production performance would need to be measured on BIC history, with agreed service labels and a backtest.”

### 45 secondes — agent et outils

Ouvrir la trace d’une question de comparaison vérifiée. Montrer les outils réellement appelés : contexte du scénario, solutions, politiques. Ne pas inventer une trace si l’écran ne la montre pas. Les outils Python et familles d’action sont définis à l’avance ; l’agent choisit les outils et quantités à évaluer, puis formule sa recommandation à partir des calculs. Les outils SQL lisent les faits de référence du portefeuille. La recherche documentaire justifie les politiques ; elle ne crée pas de règle nouvelle.

> “The question triggers retrieval and comparison. We can inspect the tools and the evidence used. The agent has no tool that can write into JDE.”

## 19:30–21:30 — validation finale et contrat cible

**Manipulation :** revenir à Carrefour, scénario initial **35 % / 4 jours**. Demander à nouveau la comparaison, sélectionner le transfert, puis **Prepare for human validation**.

Vérifier le dossier figé : compte, scénario, quantité **14 400**, coût **€287**, politiques et reliquat **700**. Cocher la revue puis **Confirm as Operations**. Recocher la revue puis **Confirm as Account manager**. Les deux rôles doivent avoir confirmé avant l’export.

> “For the rehearsal, I am playing the two reviewer roles. In production, authenticated identities and the workflow would enforce these responsibilities.”

Cliquer **Export target integration payload**, puis télécharger le JSON. Montrer `request_id`, quantité, SKU, donneur, receveur, date, coût, rôles et hash. Le statut est **EXPORT READY**, pas « envoyé à JDE ».

> “This is the reviewed decision contract that a future integration could consume. Nothing has been transmitted to JDE. Before operational execution, stock, transport and authorization would be checked again.”

Montrer **Decision follow-up** et le journal. Si un approbateur est absent, le bouton de transfert au manager existe ; cela ne contourne ni la règle de marge ni les autres approbations.

## 21:30–23:30 — conclure avec la valeur, puis JDE

### Slide 5 — Value comes from the quality of the decision.

> “The first value to measure is the time to a reviewed decision. Then we measure service coverage, incremental freight, margin discipline and the completeness of the audit trail. We are not presenting an invented ROI.”

Si le client trouve le montant de marge faible : ne pas grossir artificiellement le cas. Expliquer que l’on montre une seule semaine et quelques exceptions, et que la valeur doit être mesurée sur le volume réel de décisions. La démonstration prouve un mécanisme de décision, pas un business case annualisé.

### Slide 6 — In a BIC + JDE context…

> “JDE could remain the operational system of record. AIDP would add the analytical and agent decision layer across operational facts, forecasts and policies. The pilot would confirm the data semantics, approve the policy set, validate model performance and define the controlled hand-off.”

Le workflow EnterpriseOne / Orchestrator est une option d’architecture cible, à vérifier selon l’édition et la version Tools de BIC. Ne pas promettre un workflow transfert prêt à l’emploi ni un connecteur déjà configuré.

## Questions de réserve — en anglais

### Global

- “Which accounts have a dated coverage gap even if their risk score is not high?”
- “Which regions contain temporary gaps rather than a final firm-order deficit?”
- “Explain the difference between revenue budget, sales forecast and margin exposure.”
- “Why can the national coverage curve hide a local problem?”
- “What evidence would you need before recommending a stock transfer?”

### Carrefour

- “Why does 15,100 firm units uncovered differ from the 21,275 forecast gap?”
- “Why are you proposing 14,400 units rather than 15,100?”
- “Which warehouse gives the stock, and which commitments protect that donor?”
- “What remains unresolved after the proposed transfer?”
- “Can the risk score alone justify spending money?”

### Monoprix et autres comptes

- “Why does Monoprix need attention when the final deficit is zero?”
- “Which policy blocks the 18,000-unit transfer?”
- “Does transferring the case to a manager approve an exception?”
- “Recompare after I change the total delay to four days.”
- “Why does Leclerc appear in the action queue with a moderate probability score?”
- “For METRO, which date is uncovered and when does supply recover?”
- “What should we do for a fully covered account with a high statistical score?”

En mode AIDP ces formulations sont libres. En mode répétition, les réponses couvrent les intentions principales ; ce mode ne démontre pas les capacités linguistiques d’un LLM.

## Réponses courtes aux objections

**« C’est juste un dashboard ? »** — “The dashboard presents the facts. The agent investigates a question, retrieves the relevant evidence and policies, and explains the trade-offs. The solution cards appear after that request and are tied to the current scenario.”

**« Le modèle explique la cause ? »** — “No. The score is statistical. The explanation comes from dated receipt events and operational facts. Model contributions are not causal evidence.”

**« Zéro déficit au 31 suffit ? »** — “No. A later receipt may cover the end of the week while two earlier days remain uncovered. We evaluate the dated trajectory.”

**« Pourquoi plus de demande que de commandes ? »** — “Firm orders are commitments. The demand forecast includes anticipated demand and is floored by firm orders. A forecast-driven transfer needs commercial confirmation; it does not automatically create a new promise.”

**« L’agent peut valider ? »** — “No. It has read and analysis tools. Approval and escalation are explicit human actions in the application.”

**« Tout est dans JDE ? »** — “Not in this demo. All source data is in Object Storage. JDE is the integration context we would validate with BIC.”

## Plan de secours et raccourci

Si une réponse cloud prend plus de 30 secondes, utiliser la marge de 90 secondes et montrer les faits de la courbe pendant l’attente. Si elle échoue, dire : “The live agent is unavailable. I will use the clearly labelled rehearsal mode to explain the remaining decision flow.” Ne pas prétendre que la réponse locale vient d’AIDP.

Si vous avez deux minutes de retard, ne pas ouvrir METRO ni Leclerc ; ils sont des cas de réserve. Réduire la visite technique à une table Gold et la trace de l’agent. Conserver impérativement Monoprix, le blocage FIN-01 et la validation finale : c’est le cœur de la valeur.

**Fin à 25 minutes :** demander au client quel indicateur il souhaite mesurer dans un pilote : temps d’investigation, service, surcoût logistique ou conformité des décisions. Ne pas conclure par une promesse de gain non mesurée.

## Vérifier que la proposition est calculée pendant l’échange

En complément, hors du parcours chronométré, revenir à Carrefour avec 35 % / 4 jours et demander :

> “Evaluate an internal transfer of exactly 13,200 units. What is its margin after freight and can we approve it? Do not change the quantity.”

L’agent doit appeler `evaluate_transfer` et produire une tuile de 13 200 unités : marge **24,986 %**, FIN-01 bloquante, reliquat ferme **1 900 unités**. La quantité diffère du dimensionnement par défaut de 14 400 unités. Montrer l’heure de calcul et les outils réellement appelés. Il s’agit d’une nouvelle évaluation, jamais d’une décision approuvée. La validation reste humaine.
