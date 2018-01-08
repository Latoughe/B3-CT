# B3 - Conteneurisation
# TP 1 - Basics
But :

* appréhender et comprendre la conteneurisation
    * en particulier la conteneurisation avec le kernel GNU/Linux
* créer des conteneurs (plus ou moins) à la main (il existe tant de façon de reproduire ça)
* appréhender les éléments standardisés autour des conteneurs
    * image (ACI)
    * runtime (runc)

* comprendre certains aspects de sécurité de Docker et savoir le configurer
* utiliser `docker` + `docker-compose`
* répondre au use case de devoir faire tourner des apps packagées sous forme de conteneurs, de façon simple et relativement robuste (use case conteneurisation = packaging)


## Low-level containerization
Tout au long du TP, vous pouvez jouer à regarder ce qu'il se passe niveau namespaces/cgroups à chaque fois que vous lancez des conteneurs. (en regardant `/proc` ou avec des commandes comme `ip a` ou `ps`)

Quelques rappels dans cette optique : 

* la suite de commande `ip` est très puissante
* `mount` (entre autres) vous permet d'afficher les points de montage
* `ps -ef` ou `ps aux` permet de lister les processus au sein d'un système
* le répertoire `/proc` contient énormément d'informations quant à l'état de l'OS et du kernel 

### 1. avec `systemd-nspawn`
**Partie uniquement pour le "fun", ce sera sûrement un peu long à Ingésup, vous pouvez la zapper.**

* **caracteristiques** :
    * *`chroot` on steroids* (chroot + namespacing)
    * peut faire boot un OS complet 
    * impossible de reboot,oude toucher au kernel (chargement de modules, etc..)
    
* Debian container
    * utilisez `debootstrap` (besoin des dépôts EPEL pour l'installer
    * choisissez une distrib dans `/usr/share/debootstrap/scripts/` :)
    * pour un debian wheezy `debootstrap wheezy /deb http://deb.debian.org/debian/` vous pouvez changer l'url vers ` http://archive.ubuntu.com/ubuntu/` pour une distrib ubuntu
    * `systemd-nspawn -D /deb` pour avoir un shell dans le conteneur
    * utilisez `machinectl list` pour voir votre conteneur
    * tout ça c'est du systemd hein. `systemctl | grep machine`, vous devriez voir un scope cgroup dans lequel évolue votre conteneur. `systemd-cgls` ou `systemd-cgtop` pour mieux le voir 
    * les autres options de `systemd-nspawn` sont intéressantes, jetez un oeil ! 
    
    * avec ce répertoire, vous pouvez aussi faire un *chroot* dedans : `chroot /deb`
    
### 2. avec `runc`
* **caractéristiques** : 
    * outil standard
    * très léger et autonome
    * grosse communauté
    * standard de l'OCI
    * initié par Docker sous le nom de *libcontainer* puis légué à l'OCI
    * c'est aussi le runtime utilisé par docker
* installer `runc` (juste un paquet) et installer docker (suivez [la doc officielle](https://docs.docker.com/engine/installation/linux/docker-ce/centos/), **c'est pas dans vos dépôts**)
* démarrez le service systemd `docker`
* `docker info | grep -i runtime`

* créer un fs alpine Linux + les metadatas standardisées (standard ACI de l'initiative OCI). Pour ce faire : 
    * `mkdir -p <WORK_DIR>/rootfs`
    * se déplacer dans le répertoire `<WORKDIR>`
    * créer un fs alpine `docker export $(docker create alpine) | tar -C rootfs -xvf -`
    * générer les metadatas `runc spec` (un fichier json a pop dans le répertoire courant)
    * `runc run <NAME>` et vous avez votre container
    * `runc list` pour voir les conteneurs

### 3. avec... rien ? :)
* **partie pas obligatoire**
* **caractéristiques** : 
    * un *conteneur* c'est juste un concept, on peut l'implémenter soi-même de mille et une façons différentes
    
* on peut réutiliser les filesystems créés juste au dessus pour faire un conteneur applicatif juste avec du *systemd* (juste une unité de type *service*)
* mise en place d'isolation *namespaces* et restrictions *cgroups*
* set de *capabilities* limité
* un applicatif qui se lance en `ExecStart` (comme un nginx) dans un filesystem créé plus haut (on peut `chroot` à l'intérieur pour le configurer facilement

### 4. avec rkt
* **caractéristiques** :
    * réputé robuste & secure
    * grosse communauté
    * conforme aux standards
    * initié par coreOS
    
* *rkt* est une alternative à Docker ((initiative de CoreOS pas mal poussée par d'autres grands acteurs)
* récupérer le rpm pour centos `https://github.com/rkt/rkt/releases/download/v1.29.0/rkt-1.29.0-1.x86_64.rpm`
* installer le (`rpm -ivh <PACKAGE>`)
* *rkt* n'utilise pas de démon pour gérer les conteneurs (contrairement à docker). Rien à démarrer donc ! 
* `rkt list` pour voir les conteneurs lancés
* pour lancer une image Docker alpine dans un conteneur rkt : `rkt --insecure-options=image run docker://alpine`
* *rkt* n'utilise pas de démon donc impossible de mettre un conteneur en fond (il serait à la charge du démon... qui n'existe pas donc !). Ceci est la charge de **l'init system**. Allons-y, avec systemd : 
```
systemd-run rkt --insecure-options=image run docker://alpine --exec /bin/sleep -- 9999
# systemd-run est très puissant
```

* **note** : on peut aussi lancer les conteneurs dans des VM avec *rkt* (voir modification du "*stage1*" *rkt*)

## Docker basics
* **caractéristiques** :
    * très répandu
    * léger et désormais cross-platform 
    * très utile pour des environnements de développements
    * intégrations avec énormément d'outils

* **basic configuration**
    * installation de docker : suivez [la doc officielle](https://docs.docker.com/engine/installation/linux/docker-ce/centos/), **c'est pas dans vos dépôts**
    * unités **systemd** de type *service* et *socket*
        * pendant le démarrage du *service*, population de `/var/lib/docker`
        * et création du *socket* UNIX dédié à Docker
    * une fois le service démarré vous pouvez utiliser Docker avec `root` ou les membres du groupes `docker`. Cherchez à quel endroit exactement est apposé cette restriction. 
    * changer la configuration de base du démon docker `dockerd`
        * utilise un répertoire de travail (l'habituel `/var/lib/docker`) sur une partition LVM à la racine (`/data` par exemple)
        * changer le *OOM score* du démon (plus il est haut et plus il y a des chances qu'il se fasse détruire en premier)
    * créer une autre unité systemd `docker-tcp.service`    
        * lance une deuxième instance du démon Docker, accessible à travers un socket TCP (à travers le réseau donc)
    
* **basic operations**
    * vérifier configuration/installation : `docker info` 
        * le runtime est bien `runc` :)
    * lancer un conteneur `docker run`
        * `docker run -d alpine sleep 9999`
        * `docker run -it alpine sh`
        * essayer de lancer un conteneur dont les processus n'appartiendront pas à root 
    * quelques commandes : 
        * lister conteneurs `docker ps` ou `docker container ls`
        * lister images `docker images` ou `docker image ls`
        * lister réseaux `docker network ls`
        * `docker stats`
        
    * utiliser `-v` pour monter le répertoire `/home` de l'hôte dans un conteneur alpine
    * utiliser l'image `nginx` du dépôt library et accéder à la page d'accueil de *NGINX* sur le port 8888 de l'hôte
    * **optionnel** : lancer le conteneur *NGINX* depuis une unité *systemd* de type *service*
    
* **HTTP API**
Nan sans déc y'a un vrai intérêt. Même plusieurs. Montrer que : 
    * un socket c'est juste l'endroit où la donnée s'échange. On peut faire transiter n'importe quoi, par exemple de l'HTTP. Le démon docker attend de l'HTTP à travers un socket UNIX (par défaut)
    * c'est "programmatique" comme approche. On pourrait construire nous-même un binaire ou un client pour faire ce que l'on fait d'habitude avec la commande `docker`
    * cette API, elle est conforme aux standards. Une API similaire est présente, par exemple, sous `rkt` ou les `VIC` (d'ailleurs, avec un VIC engine, on utilise le binaire `docker` quand même pour taper dessus : VIC engine expose la même API que docker)

* utiliser l'option `--unix-socket` de `curl` pour requêter l'API HTTP de docker
    * `curl --unix-socket <PATH_TO_SOCKET> http://<URI>`
    * récupérer la liste des conteneurs actifs
    * récupérer la liste des images
    * lancer un conteneur et récupérer son IP depuis une requête `curl`
 
* **robust conf + deployment**
    * activer l'utilisation des *user namespaces* par votre kernel
    * utiliser le *user namespace remapping* du démon docker
        * test : vérifier l'appartenance de votre répertoire Docker de data (`/data` ?)
    * votre démon Docker doit utiliser [la politique `seccomp`  recommandée par le projet Moby](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json)
    * suivre [la doc officielle](https://docs.docker.com/engine/userguide/storagedriver/device-mapper-driver/#configure-direct-lvm-mode-for-production) pour mettre en place l'utilisation d'une backend `device-mapper` en `direct-lvm` (*"CONFIGURE DIRECT-LVM MODE MANUALLY"*) côté stockage
        * test : `docker info`, `df -h` à chaque lancement de conteneur
        * test2 : lancer un conteneur, exécuter un shell dedans, remplir le disque complètement. Plus aucune opération est réalisable. On peut tuer le conteneur depuis l'extérieur
    
* **Compose**

    * installer `docker-compose` en suivant la doc officielle
    * packager le code python fourni (créer une image)
    * créer un compose qui contient : 
        * un conteneur *Redis* (stockage clé/valeur)
        * un conteneur avec l'app Python packagée (qui écrit/lit des valeurs dans Redis)
        * l'app Python doit pouvoir joindre un hôte Redis avec le hostname `db` sur le port 6379
    * ouvrez un navigateur sur votre machine, rdv à `http://<IP_VM>:5000`
    * modifier le fichier `yml` et ajouter un troisième conteneur reverse proxy NGINX qui redirige vers l'interface web de l'app Python
    
    * à la fin : 
        * un conteneur de front `front` : NGINX, qui écoute sur le port 80, accessible depuis l'extérieur
        * un conteneur applicatif `app` : l'app Python, packagée par vos soins, joignable que dans le réseau de votre `docker-compose`
        * un conteneur de bdd Redis `db`, qui écoute sur le port 6379, dans lequel `app` vient écrire

* **GUI ?**
    * Déployer Portainer (ça se trouve sur github !)
    * créer un deuxième hôte Docker et le piloter depuis Portainer (socket TCP)	