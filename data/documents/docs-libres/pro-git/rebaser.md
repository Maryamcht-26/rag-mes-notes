<!-- Source : Pro Git, Scott Chacon et Ben Straub, traduction française, https://git-scm.com/book/fr/v2
     Licence : CC BY-NC-SA 3.0, https://creativecommons.org/licenses/by-nc-sa/3.0/ -->

### Rebaser (_Rebasing_)

Dans Git, il y a deux façons d'intégrer les modifications d'une branche dans une autre : en fusionnant (`merge`) et en rebasant (`rebase`).
Dans ce chapitre, vous apprendrez la signification de rebaser, comment le faire, pourquoi c'est un outil incroyable et dans quels cas il est déconseillé de l'utiliser.

Si vous revenez à un exemple précédent du chapitre , vous remarquerez que votre travail a divergé et que vous avez ajouté des _commits_ sur deux branches différentes.

Comme nous l'avons déjà expliqué, le moyen le plus simple pour intégrer ces branches est la fusion via la commande `merge`.
Cette commande réalise une _fusion à trois branches_ entre les deux derniers instantanés (_snapshots_) de chaque branche (C3 et C4) et l'ancêtre commun le plus récent (C2), créant un nouvel instantané (et un _commit_).

Cependant, il existe un autre moyen : vous pouvez prendre le _patch_ de la modification introduite en `C4` et le réappliquer sur `C3`.
Dans Git, cette action est appelée "rebaser" (_rebasing_).
Avec la commande `rebase`, vous pouvez prendre toutes les modifications qui ont été validées sur une branche et les rejouer sur une autre.

Dans cet exemple, vous lanceriez les commandes suivantes :

$ git checkout experiment
$ git rebase master
First, rewinding head to replay your work on top of it...
Applying: added staged command

Cela fonctionne en cherchant l'ancêtre commun le plus récent des deux branches (celle sur laquelle vous vous trouvez et celle sur laquelle vous rebasez), en récupérant toutes les différences introduites par chaque _commit_ de la branche courante, en les sauvant dans des fichiers temporaires, en réinitialisant la branche courante sur le même _commit_ que la branche de destination et en appliquant finalement chaque modification dans le même ordre.

À ce moment, vous pouvez retourner sur la branche `master` et réaliser une fusion en avance rapide (_fast-forward merge_).

$ git checkout master
$ git merge experiment

À présent, l'instantané pointé par `C4'` est exactement le même que celui pointé par `C5` dans l'exemple de fusion.
Il n'y a pas de différence entre les résultats des deux types d'intégration, mais rebaser rend l'historique plus clair.
Si vous examinez le journal de la branche rebasée, elle est devenue linéaire : toutes les modifications apparaissent en série même si elles ont eu lieu en parallèle.

Vous aurez souvent à faire cela pour vous assurer que vos _commits_ s'appliquent proprement sur une branche distante — par exemple, sur un projet où vous souhaitez contribuer mais que vous ne maintenez pas.
Dans ce cas, vous réaliseriez votre travail dans une branche puis vous rebaseriez votre travail sur `origin/master` quand vous êtes prêt à soumettre vos patchs au projet principal.
De cette manière, le mainteneur n'a pas à réaliser de travail d'intégration — juste une avance rapide ou simplement une application propre.

Il faut noter que l'instantané pointé par le _commit_ final, qu'il soit le dernier des _commits_ d'une opération de rebasage ou le _commit_ final issu d'une fusion, sont en fait le même instantané — c'est juste que l'historique est différent.
Rebaser rejoue les modifications d'une ligne de _commits_ sur une autre dans l'ordre d'apparition, alors que la fusion joint et fusionne les deux têtes.

Vous pouvez aussi faire rejouer votre rebasage sur autre chose qu'une branche.
Prenez un historique tel que  par exemple.
Vous avez créé une branche thématique (`server`) pour ajouter des fonctionnalités côté serveur à votre projet et avez réalisé un _commit_.
Ensuite, vous avez créé une branche pour ajouter des modifications côté client (`client`) et avez validé plusieurs fois.
Finalement, vous avez rebasculé sur la branche `server` et avez réalisé quelques _commits_ supplémentaires.

Supposons que vous décidez que vous souhaitez fusionner vos modifications du côté client dans votre ligne principale pour une publication (_release_) mais vous souhaitez retenir les modifications de la partie serveur jusqu'à ce qu'elles soient un peu mieux testées.
Vous pouvez récupérer les modifications du côté client qui ne sont pas sur le serveur (`C8` et `C9`) et les rejouer sur la branche `master` en utilisant l'option `--onto` de `git rebase` :

$ git rebase --onto master server client

Cela signifie en substance "Extraire la branche client, déterminer les patchs depuis l'ancêtre commun des branches `client` et `server` puis les rejouer sur `master` ".
C'est assez complexe, mais le résultat est assez impressionnant.

Maintenant, vous pouvez faire une avance rapide sur votre branche `master` (cf. ):

$ git checkout master
$ git merge client

Supposons que vous décidiez de tirer (_pull_) votre branche `server` aussi.
Vous pouvez rebaser la branche `server` sur la branche `master` sans avoir à l'extraire avant en utilisant `git rebase [branchedebase] [branchethematique]` — qui extrait la branche thématique (dans notre cas, `server`) pour vous et la rejoue sur la branche de base (`master`) :

$ git rebase master server

Cette commande rejoue les modifications de `server` sur le sommet de la branche `master`, comme indiqué dans .

Vous pouvez ensuite faire une avance rapide sur la branche de base (`master`) :

$ git checkout master
$ git merge server

Vous pouvez effacer les branches `client` et `server` une fois que tout le travail est intégré et que vous n'en avez plus besoin, éliminant tout l'historique de ce processus, comme visible sur  :

$ git branch -d client
$ git branch -d server

Ah… mais les joies de rebaser ne viennent pas sans leurs contreparties, qui peuvent être résumées en une ligne :

**Ne rebasez jamais des _commits_ qui ont déjà été poussés sur un dépôt public.**

Si vous suivez ce conseil, tout ira bien.
Sinon, de nombreuses personnes vont vous haïr et vous serez méprisé par vos amis et votre famille.

Quand vous rebasez des données, vous abandonnez les _commits_ existants et vous en créez de nouveaux qui sont similaires mais différents.
Si vous poussez des _commits_ quelque part, que d'autres les tirent et se basent dessus pour travailler, et qu'après coup, vous réécrivez ces _commits_ à l'aide de `git rebase` et les poussez à nouveau, vos collaborateurs devront re-fusionner leur travail et les choses peuvent rapidement devenir très désordonnées quand vous essaierez de tirer leur travail dans votre dépôt.

Examinons un exemple expliquant comment rebaser un travail déjà publié sur un dépôt public peut générer des gros problèmes.
Supposons que vous clonez un dépôt depuis un serveur central et réalisez quelques travaux dessus.
Votre historique de _commits_ ressemble à ceci :

À présent, une autre personne travaille et inclut une fusion, puis elle pousse ce travail sur le serveur central.
Vous le récupérez et vous fusionnez la nouvelle branche distante dans votre copie, ce qui donne l'historique suivant :

Ensuite, la personne qui a poussé le travail que vous venez de fusionner décide de faire marche arrière et de rebaser son travail.
Elle lance un `git push --force` pour forcer l'écrasement de l'historique sur le serveur.
Vous récupérez alors les données du serveur, qui vous amènent les nouveaux _commits_.

Vous êtes désormais tous les deux dans le pétrin.
Si vous faites un `git pull`, vous allez créer un _commit_ de fusion incluant les deux historiques et votre dépôt ressemblera à ça :

Si vous lancez `git log` lorsque votre historique ressemble à ceci, vous verrez deux _commits_ qui ont la même date d'auteur et les mêmes messages, ce qui est déroutant.
De plus, si vous poussez cet historique sur le serveur, vous réintroduirez tous ces _commits_ rebasés sur le serveur central, ce qui va encore plus dérouter les autres développeurs.
C'est plutôt logique de présumer que l'autre développeur ne souhaite pas voir apparaître `C4` et `C6` dans l'historique.
C'est la raison pour laquelle il avait effectué un rebasage initialement.

Si vous vous retrouvez effectivement dans une situation telle que celle-ci, Git dispose d'autres fonctions magiques qui peuvent vous aider.
Si quelqu'un de votre équipe pousse de force des changements qui écrasent des travaux sur lesquels vous vous êtes basés, votre défi est de déterminer ce qui est à vous et ce qui a été réécrit.

Il se trouve qu'en plus de l'empreinte SHA du _commit_, Git calcule aussi une empreinte qui est uniquement basée sur le patch introduit avec le commit.
Ceci est appelé un "identifiant de patch" (_patch-id_).

Si vous tirez des travaux qui ont été réécrits et les rebasez au-dessus des nouveaux _commits_ de votre collègue, Git peut souvent déterminer ceux qui sont uniquement les vôtres et les réappliquer au sommet de votre nouvelle branche.

Par exemple, dans le scénario précédent, si au lieu de fusionner quand nous étions à l'étape  nous exécutons la commande  `git rebase teamone/master`, Git va :

* Déterminer quels travaux sont uniques à notre branche (C2, C3, C4, C6, C7)
* Déterminer ceux qui ne sont pas des _commits_ de fusion (C2, C3, C4)
* Déterminer ceux qui n'ont pas été réécrits dans la branche de destination (uniquement C2 et C3 puisque C4 est le même _patch_ que C4')
* Appliquer ces _commits_ au sommet de `teamone/master`

Ainsi, au lieu du résultat que nous avons observé au chapitre , nous aurions pu finir avec quelque chose qui ressemblerait davantage à .

Cela fonctionne seulement si les _commits_ C4 et C4' de votre collègue correspondent presque exactement aux mêmes modifications.
Autrement, le rebasage ne sera pas capable de déterminer qu'il s'agit d'un doublon et va ajouter un autre _patch_ similaire à C4 (ce qui échouera probablement puisque les changements sont au moins partiellement déjà présents).

Vous pouvez également simplifier tout cela en lançant un `git pull --rebase` au lieu d'un `git pull` normal.
Vous pouvez encore le faire manuellement à l'aide d'un `git fetch` suivi d'un `git rebase team1/master` dans le cas présent.

Si vous utilisez `git pull` et voulez faire de `--rebase` le traitement par défaut, vous pouvez changer la valeur du paramètre de configuration `pull.rebase` par `git config --global pull.rebase true`.

Si vous considérez le fait de rebaser comme un moyen de nettoyer et réarranger des _commits_ avant de les pousser et si vous vous en tenez à ne rebaser que des _commits_ qui n'ont jamais été publiés, tout ira bien.
Si vous tentez de rebaser des _commits_ déjà publiés sur lesquels les gens ont déjà basé leur travail, vous allez au devant de gros problèmes et votre équipe vous en tiendra rigueur.

Si vous ou l'un de vos collègues y trouve cependant une quelconque nécessité, assurez-vous que tout le monde sache lancer un `git pull --rebase` pour essayer de rendre les choses un peu plus faciles.

Maintenant que vous avez vu concrètement ce que signifient rebaser et fusionner, vous devez vous demander ce qu'il est préférable d'utiliser.
Avant de pouvoir répondre à cela, revenons quelque peu en arrière et parlons un peu de ce que signifie un historique.

On peut voir l'historique des _commits_ de votre dépôt comme un *enregistrement de ce qu'il s'est réellement passé*.
Il s'agit d'un document historique qui a une valeur en tant que tel et ne doit pas être altéré.
Sous cet angle, modifier l'historique des _commits_ est presque blasphématoire puisque vous _mentez_ sur ce qu'il s'est réellement passé.
Dans ce cas, que faire dans le cas d'une série de _commits_ de fusions désordonnés ?
Cela reflète ce qu'il s'est passé et le dépôt devrait le conserver pour la postérité.

Le point de vue inverse consiste à considérer que l'historique des _commits_ est *le reflet de la façon dont votre projet a été construit*.
Vous ne publieriez jamais le premier brouillon d'un livre et le manuel de maintenance de votre projet mérite une révision attentive.
Ceci constitue le camp de ceux qui utilisent des outils tels que le rebasage et les branches filtrées pour raconter une histoire de la meilleure des manières pour les futurs lecteurs.

Désormais, nous espérons que vous comprenez qu'il n'est pas si simple de répondre à la question portant sur le meilleur outil entre fusion et rebasage.
Git est un outil puissant et vous permet beaucoup de manipulations sur et avec votre historique mais chaque équipe et chaque projet sont différents.
Maintenant que vous savez comment fonctionnent ces deux outils, c'est à vous de décider lequel correspond le mieux à votre situation en particulier.

De manière générale, la manière de profiter au mieux des deux mondes consiste à rebaser des modifications locales que vous avez effectuées mais qui n'ont pas encore été partagées avant de les pousser de manière à obtenir un historique propre mais sans jamais rebaser quoi que ce soit que vous ayez déjà poussé quelque part.
