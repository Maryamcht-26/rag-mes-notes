<!-- Source : Pro Git, Scott Chacon et Ben Straub, traduction française, https://git-scm.com/book/fr/v2
     Licence : CC BY-NC-SA 3.0, https://creativecommons.org/licenses/by-nc-sa/3.0/ -->

### Les branches en bref

Pour réellement comprendre la manière dont Git gère les branches, nous devons revenir en arrière et examiner de plus près comment Git stocke ses données.

Si vous vous souvenez bien du chapitre , Git ne stocke pas ses données comme une série de modifications ou de différences successives mais plutôt comme une série d'instantanés (appelés _snapshots_).

Lorsque vous faites un commit, Git stocke un objet _commit_ qui contient un pointeur vers l'instantané (_snapshot_) du contenu que vous avez indexé.
Cet objet contient également les noms et prénoms de l'auteur, le message que vous avez renseigné ainsi que des pointeurs vers le ou les _commits_ qui précèdent directement ce _commit_ : aucun parent pour le _commit_ initial, un parent pour un _commit_ normal et de multiples parents pour un _commit_ qui résulte de la fusion d'une ou plusieurs branches.

Pour visualiser ce concept, supposons que vous avez un répertoire contenant trois fichiers que vous indexez puis validez.
L'indexation des fichiers calcule une empreinte (_checksum_) pour chacun (via la fonction de hachage SHA-1 mentionnée au chapitre ), stocke cette version du fichier dans le dépôt Git (Git les nomme _blobs_) et ajoute cette empreinte à la zone d'index (_staging area_) :

$ git add README test.rb LICENSE
$ git commit -m 'initial commit of my project'

Lorsque vous créez le _commit_ en lançant la commande `git commit`, Git calcule l'empreinte de chaque sous-répertoire (ici, seulement pour le répertoire racine) et stocke ces objets de type arbre dans le dépôt Git.
Git crée alors un objet _commit_ qui contient les méta-données et un pointeur vers l'arbre de la racine du projet de manière à pouvoir recréer l'instantané à tout moment.

Votre dépôt Git contient à présent cinq objets :
un _blob_ pour le contenu de chacun de vos trois fichiers, un arbre (_tree_) qui liste le contenu du répertoire et spécifie quels noms de fichiers sont attachés à quels _blobs_ et enfin un objet _commit_ portant le pointeur vers l'arbre de la racine ainsi que toutes les méta-données attachées au _commit_.

Si vous faites des modifications et validez à nouveau, le prochain _commit_ stocke un pointeur vers le _commit_ le précédant immédiatement.

Une branche dans Git est simplement un pointeur léger et déplaçable vers un de ces _commits_.
La branche par défaut dans Git s'appelle `master`.
Au fur et à mesure des validations, la branche `master` pointe vers le dernier des _commits_ réalisés.
À chaque validation, le pointeur de la branche `master` avance automatiquement.

La branche ``master`` n'est pas une branche spéciale.
Elle est identique à toutes les autres branches.
La seule raison pour laquelle chaque dépôt en a une est que la commande `git init` la crée par défaut et que la plupart des gens ne s'embêtent pas à la changer.

Que se passe-t-il si vous créez une nouvelle branche ?
Eh bien, cela crée un nouveau pointeur pour vous.
Supposons que vous créez une nouvelle branche nommée `test`.
Vous utilisez pour cela la commande `git branch` : 

$ git branch testing

Cela crée un nouveau pointeur vers le _commit_ courant.

Comment Git connaît-il alors la branche sur laquelle vous vous trouvez ?
Il conserve à cet effet un pointeur spécial appelé `HEAD`.
Vous remarquez que sous cette appellation se cache un concept très différent de celui utilisé dans les autres VCS tels que Subversion ou CVS.
Dans Git, il s'agit simplement d'un pointeur sur la branche locale où vous vous trouvez.
Dans ce cas, vous vous trouvez toujours sur `master`.
En effet, la commande `git branch` n'a fait que créer une nouvelle branche — elle n'a pas fait basculer la copie de travail vers cette branche.

Vous pouvez vérifier cela facilement grâce à la commande `git log` qui vous montre vers quoi les branches pointent.
Il s'agit de l'option `--decorate`.

$ git log --oneline --decorate
f30ab (HEAD, master, test) add feature #32 - ability to add new
34ac2 fixed bug #ch1328 - stack overflow under certain conditions
98ca9 initial commit of my project

Vous pouvez voir les branches ``master``  et ``test`` qui se situent au niveau du _commit_ `f30ab`.

Pour basculer sur une branche existante, il suffit de lancer la commande `git checkout`.
Basculons sur la nouvelle branche `testing` :

$ git checkout testing

Cela déplace `HEAD` pour le faire pointer vers la branche `testing`.

Qu'est-ce que cela signifie ?
Et bien, faisons une autre validation :

$ vim test.rb
$ git commit -a -m 'made a change'

C'est intéressant parce qu'à présent, votre branche `testing` a avancé tandis que la branche `master` pointe toujours sur le _commit_ sur lequel vous étiez lorsque vous avez lancé la commande `git checkout` pour changer de branche.
Retournons sur la branche `master` :

$ git checkout master

.`git log` ne montre pas _toutes_ les branches _tout_ le temps
Si vous alliez lancer `git log` maintenant, vous pourriez vous demander où se trouve la branche « testing » que vous avez tout juste créée, car elle n'apparaît pas dans la sortie.

La branche n'a pas disparu ; Git ne sait juste pas que cette branche vous intéresse et il essaie de vous montrer ce qu'il pense être le plus pertinent.
Autrement dit, par défaut, `git log` ne montre que l'historique des commits sous la branche qui est extraite.

Pour montrer l'historique des commites de la branche désirée, vous devez la spécifier explicitement : `git log testing`.
Pour afficher toutes les branches, ajoutez l'option `--all` à la commande `git log`.

Cette commande a réalisé deux actions.
Elle a remis le pointeur `HEAD` sur la branche `master` et elle a replacé les fichiers de votre répertoire de travail dans l'état du _snapshot_ pointé par `master`.
Cela signifie aussi que les modifications que vous réalisez à partir de ce point divergeront de l'ancienne version du projet.
Cette commande annule les modifications réalisées dans la branche `testing` pour vous permettre de repartir dans une autre direction.

Il est important de noter que lorsque vous changez de branche avec Git, les fichiers de votre répertoire de travail sont modifiés.
Si vous basculez vers une branche plus ancienne, votre répertoire de travail sera remis dans l'état dans lequel il était lors du dernier _commit_ sur cette branche.
Si git n'est pas en mesure d'effectuer cette action proprement, il ne vous laissera pas changer de branche.

Réalisons quelques autres modifications et validons à nouveau :

$ vim test.rb
$ git commit -a -m 'made other changes'

Maintenant, l'historique du projet a divergé (voir ).
Vous avez créé une branche et basculé dessus, y avez réalisé des modifications, puis vous avez rebasculé sur la branche principale et réalisé d'autres modifications.
Ces deux modifications sont isolées dans des branches séparées : vous pouvez basculer d'une branche à l'autre et les fusionner quand vous êtes prêt.
Et vous avez fait tout ceci avec de simples commandes : `branch`, `checkout` et `commit`.

Vous pouvez également voir ceci grâce à la commande `git log`.
La commande `git log --oneline --decorate --graph --all` va afficher l'historique de vos _commits_, affichant les endroits où sont positionnés vos pointeurs de branche ainsi que la manière dont votre historique a divergé.

$ git log --oneline --decorate --graph --all
* c2b9e (HEAD, master) made other changes
| * 87ab2 (test) made a change
|/
* f30ab add feature #32 - ability to add new formats to the
* 34ac2 fixed bug #ch1328 - stack overflow under certain conditions
* 98ca9 initial commit of my project

Parce qu'une branche Git n'est en fait qu'un simple fichier contenant les 40 caractères de l'empreinte SHA-1 du _commit_ sur lequel elle pointe, les branches ne coûtent quasiment rien à créer et à détruire.
Créer une branche est aussi simple et rapide qu'écrire 41 caractères dans un fichier (40 caractères plus un retour chariot).

C'est une différence de taille avec la manière dont la plupart des VCS gèrent les branches, qui implique de copier tous les fichiers du projet dans un second répertoire.
Cela peut durer plusieurs secondes ou même quelques minutes selon la taille du projet, alors que pour Git, le processus est toujours instantané.
De plus, comme nous enregistrons les parents quand nous validons les modifications, la détermination de l'ancêtre commun approprié pour la fusion est réalisée automatiquement pour nous et est généralement une opération très facile.
Ces fonctionnalités encouragent naturellement les développeurs à créer et utiliser souvent des branches.

Voyons pourquoi vous devriez en faire autant.

Il est habituel de créer une nouvelle branche et de vouloir basculer sur cette nouvelle branche en même temps -- ça peut être réalisé en une seule opération avec `git checkout -b <nouvelle-branche>`.

Depuis Git version 2.23, on peut utiliser `git switch` au lieu de `git checkout` pour :

- basculer sur une branche existante : `git switch testing-branch`,
- créer une branche et basculer dessus ; `git switch -c nouvelle-branche`; le drapeau `-c` signifie créer, vous pouvez aussi utiliser le drapeau complet `--create`,
- revenir sur votre branche précédemment extraite : `git switch -`.
