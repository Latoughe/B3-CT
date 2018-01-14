#  B3 - Conteneurisation

# TP 1.5 - Remake

But :   

* appréhender et comprendre la conteneurisation
    * en particulier la conteneurisation avec le kernel GNU/Linux

* appréhender les éléments standardisés autour des conteneurs
    * image (ACI)
    * runtime (runc)

* comprendre certains aspects de sécurité de Docker et savoir le configurer

* utiliser docker + docker-compose

* répondre au use case de devoir faire tourner des apps packagées sous forme de conteneurs, de façon simple et relativement robuste (use case conteneurisation = packaging)

# Low level containerization
Tout au long du TP, vous pouvez jouer à regarder ce qu'il se passe niveau kernel à chaque fois que vous lancez des conteneurs. (en regardant `/proc` ou avec des commandes comme `ip a` ou `ps`)

Quelques rappels dans cette optique :

* la suite de commande `ip` est très puissante
* `mount` (entre autres) vous permet d'afficher les points de montage
* `ps -ef` ou `ps aux` permet de lister les processus au sein d'un système
* le répertoire `/proc` contient énormément d'informations quant à l'état de l'OS et du kernel

1. avec runc

**Caractéristiques** :

* outil standard
* très léger et autonome
* grosse communauté
* standard de l'OCI
* initié par Docker sous le nom de libcontainer puis légué à l'OCI
* c'est aussi le runtime utilisé par docker


* installer : 
    * `runc` (juste un paquet)
    * `docker` (suivez la doc officielle **scrupuleusement**, c'est pas dans vos dépôts. Install classique de docker-ce, pas de dépôts edge, install simple :) )

* démarrez le service systemd  `docker.service` avec le binaire `systemctl`

* la commande `docker info` donne plsuieurs informations sur votre démon docker, y compris le runtime utilisé. Utilisez la pour voir le runtime utilisé (normalement par défaut docker utilise `runc` le standard de l'OCI)

* à l'aide uniquement de `runc` (sans docker), on peut créer un conteneur. Pour ça on a besoin d'un filesystem et de metadatas au format ACI. 
* `mkdir -p <WORK_DIR>/rootfs`
* se déplacer dans le répertoire `<WORKDIR>`
* pour créer un fs alpine, utiliser la commande suivante :  `docker export $(docker create alpine) | tar -C rootfs -xvf -` (mp moi pour plus d'infos)
* générer les metadatas depuis le répertoire `<WORKDIR>` : `runc spec` (un fichier json a pop dans le répertoire courant normalement)
* `runc run <NAME>` et vous avez votre container qui porte le nom `<NAME>`

2. avec rkt

* **Caractéristiques** :

* réputé robuste & secure
* grosse communauté
* conforme aux standards
* initié par coreOS
* rkt est une alternative à Docker (initiative de CoreOS pas mal poussée par d'autres grands acteurs)

* mettre en place `rkt`
    * récupérer le rpm pour CentOS `https://github.com/rkt/rkt/releases/download/v1.29.0/rkt-1.29.0-1.x86_64.rpm` (utiliser `curl` ou `wget` pour récupérer le fichier)
    * installer le paquet (`rpm -ivh <PACKAGE>`)
    * `rkt` n'utilise pas de démon pour gérer les conteneurs (contrairement à docker). Rien à démarrer donc !
    * `rkt list` pour voir les conteneurs lancés

* la ligne de commande `rkt` est un peu moins intuitive que docker. Ceci est justifié par des cas d'utilisation différents, nous y reviendrons. 
    * référez-vous à la [doc officielle](https://coreos.com/rkt/docs/latest/commands.html) pour plus de détails sur la ligne de commande
    * `rkt run` pour lancer un conteneur
    * Pour lancer une image Docker alpine dans un conteneur rkt : `rkt --insecure-options=image run docker://alpine`

* rkt n'utilise pas de démon donc impossible de mettre un conteneur en fond (il serait à la charge du démon... qui n'existe pas donc !). Ceci est la charge de l'init system. 
* systemd est le système d'init par défaut sur notre version de CentOS, on peut l'utiliser pour lancer des processus en utilisant `systemd-run` :
    *  `systemd-run sleep 999` lance un processus `sleep` comme un service systemd. Vous obtenez le nom de l'unité au lancement (vous pouvez `systemctl status` dessus)  
    * `systemd-run rkt --insecure-options=image run docker://alpine --exec /bin/sleep -- 9999` permet de lancer une image Docker qui contient un Alpine Linux, et demander à celui de lancer le processus `sleep`
    * pour rappel, un conteneur c'est juste un concept : un processus encapsulé dans une boîte (quelque soit la nature de la boîte)
    
* **NOTE** : on peut aussi lancer les conteneurs dans des VM avec rkt ([voir modification du "stage1" rkt)](https://coreos.com/rkt/docs/latest/running-kvm-stage1.html)

# Docker basics

* **Caractéristiques** :

* très répandu
* léger et désormais cross-platform
* très utile pour des environnements de développements
* intégrations avec énormément d'outils

Dans cette partie on s'intéressera à plusieurs aspects de docker :
* côté système : configuration du démon
* un peu de sécu
* côté utilisateur : lancer quelques commande `docker` 
    * manipulation de conteneurs, volumes, réseau
    * `docker-compose`

## 1. Basic configuration

* installation de docker (déjà fait normalement) : suivez la doc officielle, c'est pas dans vos dépôts
* unités systemd de type service et socket
    * vous pouvez faire `systemctl status docker.socket` par exemple
    * quand vous lancerez le service, le répertoire `/var/lib/docker` se remplira
    * et création du socket UNIX dédié à Docker (voir l'unité `docker.socket` pour plus d'infos)
    * une fois le service démarré vous pouvez utiliser Docker avec root ou les membres du groupe `docker`. Cherchez à quel endroit exactement est apposé cette restriction (c'et l'endroit qui vous permet de communiquer avec le démon docker).
    
* changement la configuration de base du démon docker `dockerd`
    * soit en modifiant le fichier de configuration (format json)
    * soit en modifiant directement la ligne `ExecStart` de l'unité systemd 
    
    * changer le répertoire de travail de docker : utilise un répertoire de travail (l'habituel `/var/lib/docker`) pour un répertoire `/data` créé à la racine. Pour les plus chauds : montez une partition LVM à cet endroit.
    * changer le OOM score du démon (plus il est haut et plus il y a des chances qu'il se fasse détruire en premier)
    * créer une autre unité systemd `docker-tcp.service`. Elle lance une deuxième instance du démon Docker, accessible à travers un socket TCP (à travers le réseau donc) 

## 2. Basic operations

* vérifier configuration/installation : docker info
    * le runtime est bien runc :)

* lancer un conteneur `docker run`
    * `docker run -d alpine sleep 9999`
    * `docker run -it alpine sh`
    * essayer de lancer un conteneur dont les processus n'appartiendront pas à root

* quelques commandes :
    * lister conteneurs `docker ps` ou `docker container ls`
    * lister images `docker images` ou `docker image ls`
    * lister réseaux `docker network ls`
    * je vous laisse deviner la commande pour les `volumes`

* `docker stats` est cool

* TODO (utui:
    * utiliser `-v` de `docker run` pour monter le répertoire `/home` de l'hôte dans un conteneur `alpine`
    * utiliser `-v` de `docker run` pour monter la page html d'accueil d'un conteneur `nginx`, et `-p` pour accéder à cette page d'accueil depuis un navigateur ur votre machine hôte 

## 3. HTTP API 
**Nan sans déc y'a un vrai intérêt. Même plusieurs.** Montrer que :
* approfondir un peu la notion de socket : c'est juste l'endroit où la donnée s'échange. On peut faire transiter n'importe quoi, par exemple de l'HTTP. Le démon docker attend de l'HTTP à travers un socket UNIX (par défaut)
* c'est "programmatique" comme approche. On pourrait construire nous-même un binaire ou un client pour faire ce que l'on fait d'habitude avec la commande docker
cette API, elle est conforme aux standards. Une API similaire est présente, par exemple, sous rkt ou les VIC (d'ailleurs, avec un VIC engine, on utilise le binaire docker quand même pour taper dessus : VIC engine expose la même API que docker)

* **Exploration manuelle** de l'API HTTP docker (conforme standards) en utilisant l'option `--unix-socket` de `curl`
    * `curl --unix-socket <PATH_TO_SOCKET> http://<URI>`
    * récupérer la liste des conteneurs actifs
    * récupérer la liste des images
    * lancer un conteneur et récupérer son IP depuis une requête `curl`
    
   
## 4. Robust conf

Partie orientée système. L'objectif est de rendre un peu plus robuste un démon docker. Ceci n'est pas du tout exhaustif mais couvre déjà plusieurs points sensibles. 

* mettre en place l'utilisation des user namespaces par docker : 
    * activer l'utilisation des user namespaces par votre kernel
    * utiliser le user namespace remapping du démon docker
    * test : vérifier l'appartenance de votre répertoire Docker de data (/data ?)
* votre démon Docker doit utiliser la politique seccomp recommandée par le projet Moby

* suivre la doc officielle pour mettre en place l'utilisation d'une backend device-mapper en direct-lvm ("CONFIGURE DIRECT-LVM MODE MANUALLY") côté stockage
    * test : `docker info`, `df -h` à chaque lancement de conteneur
    * test2 : lancer un conteneur, exécuter un shell dedans, remplir le disque complètement. Plus aucune opération est réalisable. On peut tuer le conteneur depuis l'extérieur

* explorer les options de `docker run` et observer celles qui sont intéressantes côté sécu

## 5. Compose

* installer `docker-compose` en suivant la doc officielle

* packager le code python fourni (créer une image)
    * rédiger un Dockerfile en partant de l'image
    * le code python a besoin de certaines dépendances. Elles sont dans le dossier fourni, dans le ficier `requirements`
    * vous pouvez les installer en utilisant `pip` : 

* créer un `docker-compose.yml` qui contient :
    * un conteneur Redis (stockage clé/valeur)
    * un conteneur avec l'app Python packagée (qui écrit/lit des valeurs dans Redis)
    * l'app Python doit pouvoir joindre un hôte Redis avec le hostname `db` et `db.b3.ingesup` sur le port 6379
* ouvrez un navigateur sur votre machine, rdv à http://<IP_VM>:5000

* modifier le fichier yml et ajouter un troisième conteneur reverse proxy NGINX qui redirige vers l'interface web de l'app Python

* **à la fin** :

* un conteneur de front front : NGINX, qui écoute sur le port 80, accessible depuis l'extérieur
* un conteneur applicatif app : l'app Python, packagée par vos soins, joignable que dans le réseau de votre docker-compose
* un conteneur de bdd Redis db, qui écoute sur le port 6379, dans lequel app vient écrire
* c'est un compose typique :
    * il est autonome : il n'a besoin de rien d'autre pour fonctionner
    * il est scalable : on peut le dupliquer et certaines des unités peuvent elles-aussi être dupliquées facilement à l'intérieur
    * on pourrait faire un cluster redis plutôt qu'un seul noeud et changer les configurations du serveur applicatif et reverse proxy pour le rendre plus robuste et l'adapter à des besoins spécifiques


## 6. GUI ?

* Déployer Portainer (ça se trouve sur github !)
* créer un deuxième hôte Docker (deuxième VM) et le piloter depuis Portainer (socket TCP)