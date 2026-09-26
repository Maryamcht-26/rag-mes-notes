<!-- Source : Documentation officielle Kubernetes (FR), https://kubernetes.io/fr/docs/concepts/overview/components/
     Licence : CC BY 4.0 — The Kubernetes Authors, https://creativecommons.org/licenses/by/4.0/ -->

Cette page fournit un aperçu général des composants essentiels qui constituent un cluster Kubernetes.

## Composants principaux

Un cluster Kubernetes est composé d'un plan de contrôle et d'un ou plusieurs nœuds de travail.
Voici un bref aperçu des principaux composants :

### Composants du plan de contrôle

Gèrent l'état global du cluster :

kube-apiserver
: Le serveur principal qui expose l'API HTTP de Kubernetes

etcd
: Un magasin de clés-valeurs cohérent et hautement disponible pour toutes les données du serveur API

kube-scheduler
: Recherche les Pods qui ne sont pas encore liés à un nœud et attribue chaque Pod à un nœud approprié.

kube-controller-manager
: Exécute des contrôleurs pour mettre en œuvre le comportement de l'API Kubernetes.

cloud-controller-manager (optionnel)
: S'intègre aux fournisseurs de cloud sous-jacents.

### Composants des nœuds

S'exécutent sur chaque nœud, maintiennent les pods en cours d'exécution et fournissent l'environnement d'exécution Kubernetes :

kubelet
: Veille à ce que les Pods s'exécutent, y compris leurs conteneurs.

kube-proxy (optionnel)
: Maintient les règles réseau sur les nœuds pour mettre en œuvre les Services.

Runtime de conteneur
: Logiciel responsable de l'exécution des conteneurs. Lisez
  Runtimes de conteneurs pour en savoir plus.

Votre cluster peut nécessiter des logiciels supplémentaires sur chaque nœud ; par exemple, vous pouvez également
exécuter systemd sur un nœud Linux pour superviser les composants locaux.

## Extensions

Les extensions étendent les fonctionnalités de Kubernetes. Quelques exemples importants incluent :

DNS
: Pour la résolution DNS à l'échelle du cluster

Interface utilisateur Web (Tableau de bord)
: Pour la gestion du cluster via une interface web

Surveillance des ressources des conteneurs
: Pour collecter et stocker les métriques des conteneurs

Journalisation au niveau du cluster
: Pour enregistrer les journaux des conteneurs dans un référentiel de journaux centralisé

## Flexibilité dans l'architecture

Kubernetes permet une flexibilité dans la façon dont ces composants sont déployés et gérés.
L'architecture peut être adaptée à différents besoins, des environnements de développement réduits
aux déploiements de production à grande échelle.

Pour plus d'informations détaillées sur chaque composant et les différentes façons de configurer votre
architecture de cluster, consultez la page Architecture du cluster.
