# Regard Critique et Pistes d'Amélioration (Performance & UX)

Ce document dresse un bilan critique des performances de l'application NewsFoundry, tant sur la pertinence des réponses de l'IA que sur l'expérience utilisateur (UX), et propose trois pistes concrètes d'optimisation.

## 1. Piste d'amélioration : Fluidité via le Streaming des réponses LLM

**Constat et Justification :** 
Actuellement, lorsque l'utilisateur pose une question complexe ou génère une revue de presse, l'interface affiche un indicateur de chargement (spinner) jusqu'à ce que la totalité de la réponse soit générée par le modèle Mistral. Une revue de presse peut prendre entre 10 et 20 secondes à être générée. Selon les standards d'UX, un temps de réponse acceptable avant un premier feedback visuel est de moins de 2 secondes ; au-delà, l'utilisateur a l'impression que l'application a "planté".

**Réalisation détaillée (Streaming) :**
Pour offrir une expérience similaire à ChatGPT (où le texte s'écrit en temps réel) :
1. **Backend (FastAPI & PydanticAI) :** Remplacer l'appel `agent.run()` par `agent.run_stream()`. Modifier la route FastAPI pour retourner une `StreamingResponse` (Server-Sent Events).
2. **Frontend (Next.js) :** Au lieu d'attendre le `.json()` complet, utiliser l'API `ReadableStream` de JavaScript pour lire la réponse par petits morceaux (*chunks*) et mettre à jour l'état React (`setMessages`) à chaque morceau reçu.

## 2. Piste d'amélioration : Observabilité et Tracing avec MLflow

**Constat et Justification :**
L'application repose sur des prompts complexes (intégration du contexte WorldNewsAPI, RAG via LlamaIndex). Si l'IA commence à "halluciner" ou à donner de mauvais résultats, il est actuellement très difficile de débugger en production. Nous manquons de métriques précises sur la latence exacte de l'API Mistral versus le temps de scraping des articles.

**Réalisation détaillée (Intégration MLflow) :**
Déployer un serveur MLflow et l'intégrer au backend FastAPI.
1. Utiliser `mlflow.pydantic_ai.autolog()` qui instrumente automatiquement l'agent PydanticAI.
2. Dans l'interface MLflow, nous pourrons visualiser sous forme de "Traces" (Tracing) l'arbre d'exécution exact : 
   - Le temps passé par `WorldNewsAPI` pour trouver les URLs.
   - Le prompt exact envoyé à Mistral.
   - Le coût en tokens et la latence de génération.
Cela permettra de passer d'une logique "l'utilisateur se plaint que c'est lent" à une optimisation ciblée du goulot d'étranglement.

## 3. Piste d'amélioration : Temps de génération des Revues de Presse (Scraping Asynchrone)

**Constat et Justification :**
Le temps de génération d'une revue de presse augmente drastiquement en fonction du nombre d'URLs stockées dans l'historique du chat. Actuellement, LlamaIndex utilise `SimpleWebPageReader` qui va télécharger le contenu HTML de chaque article de manière séquentielle avant même de commencer la synthèse par l'IA. Si 5 articles mettent chacun 2 secondes à charger, on perd déjà 10 secondes.

**Réalisation détaillée (Parallélisation) :**
1. **Mesure :** Utiliser MLflow pour chronométrer l'étape spécifique de `reader.load_data(urls)`.
2. **Optimisation :** Remplacer le scraping séquentiel par des requêtes asynchrones parallèles (ex: avec `httpx.AsyncClient` combiné à `asyncio.gather()`) pour télécharger les 5 articles simultanément. Le temps de récupération des données sera ainsi égal au temps de l'article le plus lent (ex: 2 secondes au lieu de 10 secondes), réduisant le temps de génération global de 40 à 50 %.
