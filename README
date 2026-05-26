# SAO-CP

## Inspiration
Dans des environnements critiques tels que les CHU (Centres hospitaliers universitaires), les plateformes de traitement des dossiers médicaux sont des cibles privilégiées pour les attaques de type cyber. Les équipes de sécurité sont confrontées à un dilemme : l'analyse manuelle des journaux est trop lente pour répondre aux menaces actuelles, mais le confier à un AI pour bloquer les menaces est trop risqué. Une fausse alarme d'un AI autonomes pourrait accidentellement verrouiller un médecin d'un dossier médical vital pendant une urgence. SAO-CP a été créé à partir de cette exigence précise : créer un modèle de sécurité où la vitesse de l'IA répond à la sagesse humaine.

## Fonctionnalités
SAO-CP est une plateforme de sécurité qui protège une plateforme de dossiers médicaux en intégrant un agent AI sous surveillance stricte. Elle fonctionne via un workflow clair à 5 étapes :

1. **Génération et capture :** Les personnels médicaux interagissent avec la plateforme de dossiers médicaux. Toutes les actions génèrent des journaux qui sont transmis en temps réel à Splunk.
2. **Analyse agentic :** Un agent AI, connecté à Splunk via le protocole MCP, analyse en continu ces journaux. Si il détecte une anomalie (par exemple, une extorsion de données non conventionnelle), il analyse le contexte.
3. **Proposition d'action :** Au lieu d'agir aveuglément, l'agent formule une suggestion de réparation (par exemple, "Bloquer l'adresse IP de l'utilisateur" ou "Révoquer la session").
4. **Supervision humaine :** L'alerte et la suggestion de l'agent apparaissent sur un tableau de bord SOC dédié pour les analystes de sécurité. L'analyste voit exactement *pourquoi* l'agent veut agir.
5. **Validation et exécution :** Le responsable a toujours le dernier mot. En cliquant simplement, l'analyste valide l'alerte ou annule l'action. L'agent n'exécute la tâche de réparation qu'après cette validation explicite.

## Construction
Nous développons un MVP propre, hautement structuré basé sur une architecture à 4 couches :

* **Application cible :** Une application web développée avec Next.js qui simule une plateforme de dossiers médicaux. Elle émet des journaux en format JSON.
* **Splunk Enterprise :** Le moteur principal. Il ingère les journaux de l'application cible, les stocke et permet à l'agent AI de les interroger en utilisant SPL.
* **Agent AI et MCP Splunk :** Développé avec LangChain en Python, l'agent utilise le serveur MCP Splunk pour interagir directement avec Splunk, effectuer des recherches pour détecter des anomalies et formuler des suggestions basées sur le contexte. Les états et décisions de l'agent sont stockés dans une base de données PostgreSQL.
* **Tableau de bord SOC et arrière-plan :** Une interface utilisateur Next.js couplée avec un serveur backend FastAPI. FastAPI Orchestra les communications entre l'agent, la base de données et l'interface utilisateur via des WebSockets pour afficher les alertes en temps réel et capturer la validation de l'analyste.

## Architecture

![Architecture](/home/levi/Downloads/architecture.png)

