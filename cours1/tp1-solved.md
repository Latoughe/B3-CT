# B3 - Conteneurisation 

# TP 1.5 Remake

## Mise en place du lab
* installation d'une VM CentOS 7.4
* désactivation de SELinux : 
```
$ setenforce 0 && sed -i 's/enforcing/permissive/g' /etc/selinux/config
```	
* installation de certains paquets nécessaires à la réalisation du TP 
    * prérequis Docker 
        * `yum-utils` permet d'ajouter le dépôt Docker simplement
        * `device-mapper-persistent-data` permet de gérer la backend de stockage de Docker
        * `lvm2` permet de mettre en place des partitions logiques qui peuvent être utilisées par Docker
    * `runc` le runtime standard de l'OCI
    * récupération de `vim` pour le confort
  
## 1. Avec runc

* installation de `runc` et `docker` en prérequis
* vérification du runtime utilisé par docker : 

```
$ docker info | grep -i runtime
Runtimes: runc
Default Runtime: runc
```

* création d'un répertoire de travail, et d'un sous répertoire `rootfs` : `mkdir -p /srv/TP1/runc/rootfs`

* récupération d'un filesystem alpine dan le répertoire `rootfs`, à l'aide du binaire `docker` : 
```
$ cd /srv/TP1/runc/ &&  docker export $(docker create alpine) | tar -C rootfs -xvf -
```
 
* générer les metadatas standadisées afin de récupérer une image standard ACI (filesystem + metadatas standardisées = image ACI) :
```
$ pwd
/srv/TP1/runc
$ ls
rootfs

$ runc spec
$ ls
config.json  rootfs
```

* le fichier `config.json`   contient l'ensemble des informations que pourraient notamment contenir un Dockerfile. Comme par exemple la commande lancée au démarrage du conteneur. On va modifier le `config.json` pour que notre conteneur runc lance un `sleep` :
```
[...]
                "args": [
                        "sleep",
                        "99999"
                ],
[...]
```

* une fois fait, on peut lancer le conteneur depuis le répertoire contenant `config.json` : `runc run toto`

* observons `ns` et `cgroups` utilisés
 
```
$ runc list
ID          PID         STATUS      BUNDLE          CREATED                          OWNER
toto        1639        running     /srv/TP1/runc   2018-01-17T09:41:01.636041686Z   root

$ **ps -ef | grep sleep**
root      1639  1634  0 10:41 pts/0    00:00:00 sleep 99999
it4       1659  1536  0 10:41 pts/1    00:00:00 grep --color=auto sleep

$ ls /proc/1639/ns -al
total 0
dr-x--x--x. 2 root root 0 17 janv. 10:41 .
dr-xr-xr-x. 9 root root 0 17 janv. 10:41 ..
lrwxrwxrwx. 1 root root 0 17 janv. 10:41 ipc -> ipc:[4026532181]
lrwxrwxrwx. 1 root root 0 17 janv. 10:41 mnt -> mnt:[4026532179]
lrwxrwxrwx. 1 root root 0 17 janv. 10:41 net -> net:[4026532184]
lrwxrwxrwx. 1 root root 0 17 janv. 10:41 pid -> pid:[4026532182]
lrwxrwxrwx. 1 root root 0 17 janv. 10:41 user -> user:[4026531837]
lrwxrwxrwx. 1 root root 0 17 janv. 10:41 uts -> uts:[4026532180]

$ ls /proc/$$/ns -al
total 0
dr-x--x--x. 2 it4 it4 0 17 janv. 10:34 .
dr-xr-xr-x. 9 it4 it4 0 17 janv. 10:34 ..
lrwxrwxrwx. 1 it4 it4 0 17 janv. 10:34 ipc -> ipc:[4026531839]
lrwxrwxrwx. 1 it4 it4 0 17 janv. 10:34 mnt -> mnt:[4026531840]
lrwxrwxrwx. 1 it4 it4 0 17 janv. 10:34 net -> net:[4026531956]
lrwxrwxrwx. 1 it4 it4 0 17 janv. 10:34 pid -> pid:[4026531836]
lrwxrwxrwx. 1 it4 it4 0 17 janv. 10:34 user -> user:[4026531837]
lrwxrwxrwx. 1 it4 it4 0 17 janv. 10:34 uts -> uts:[4026531838]

$ systemd-cgtop # affiche un cgroup 'toto', présent aussi dans /sys/fs/cgroup/memory/toto par exemple
```

## 2. Avec rkt

* création d'un répertoire de travail : 
```
$ mkdir -p /srv/TP1/rkt
```

* récupération du paquet 
```
$ curl -SLO https://github.com/rkt/rkt/releases/download/v1.29.0/rkt-1.29.0-1.x86_64.rpm
```

* installation du paquet 
```
$ sudo rpm -ivh rkt-1.29.0-1.x86_64.rpm 
```

* création d'un répertoire de test qui sera monté dans le conteneur
```

```

* lancement du conteneur :
```
$ rkt run --insecure-options=image --volume rkt-test,kind=host,source=/tmp/rkt-test,readOnly=false --mount volume=rkt-test,target=/data/  docker://alpine --exec ls -- /data[ 2953.971257] alpine[6]: yo
$ rkt run --insecure-options=image --volume rkt-test,kind=host,source=/tmp/rkt-test,readOnly=false --mount volume=rkt-test,target=/data/  docker://alpine --exec cat -- /data/yo
[ 2963.395434] alpine[6]: rkt-test
```

* explication : 
    * `--insecure-options=image` : rkt n'accepte que des images ACI. Ici on récupère dynamiquement une image Docker : on doit préciser à rkt que l'image est non-sécurisée
    * `--volume` permet de créer et définir à la volée un volume. Ici nous utilisont le répertoire `/tmp/rkt-test` de l'hôte comme source
    * `--mount` permet de monter un volume à l'intérieur du conteneur, ici on se servira du volume créé à la volée précédemment
    * `docker://alpine` permet de récupérer une image Docker sur le Hub
    * `--exec` permet de définir la commande exécutée par le conteneur
    * `--` permet de dire à rkt que la ligne est terminée, ce qui est mis après sera joutée à la commande passée en `--exec`
    * pour ceux qui ont l'habitude avec docker, nous aurions fait quelque chose du genre poru arriver au même résultat : 
```
$ docker run -v /tmp/rkt-test:/data alpine ls /data
```

* lancement d'un conteneur et entretien de ce dernier avec `systemd`. Déléguer cette tâche à `systemd` permet notammet de se passer d'un démon central comme docker et son `dockerd`
    * on utilise `systemd-run` qui transforme toute commande en une unité `systemd` de type service
```
$ rkt list
UUID	APP	IMAGE NAME	STATE	CREATED	STARTED	NETWORKS

$ systemd-run rkt --insecure-options=image run docker://alpine --exec /bin/sleep -- 9999
Running as unit run-1566.service.

$ rkt list
UUID		APP	IMAGE NAME					STATE	CREATED		STARTED		NETWORKS
14affdb0	alpine	registry-1.docker.io/library/alpine:latest	running	1 second ago	1 second ago	default:ip4=172.16.28.2

$ systemctl status run-1566.service
● run-1566.service - /bin/rkt --insecure-options=image run docker://alpine --exec /bin/sleep -- 9999
   Loaded: loaded (/run/systemd/system/run-1566.service; static; vendor preset: disabled)
  Drop-In: /run/systemd/system/run-1566.service.d
           └─50-Description.conf, 50-ExecStart.conf
   Active: active (running) since mer. 2018-01-17 11:18:38 CET; 8s ago
 Main PID: 1567 (ld-linux-x86-64)
   Memory: 6.2M
   CGroup: /system.slice/run-1566.service
[...]

# On voit au dessus que le slice utilisé par notre unité est /system.slice/run-1566.service : un nouvel espace de restriction CGroup a bien été créé

$ ps -ef | grep sleep 
root      1605  1598  0 11:18 ?        00:00:00 /bin/sleep 9999
root      1629  1335  0 11:21 pts/0    00:00:00 grep --color=auto sleep

$ ls -al /proc/1605/ns
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 ipc -> ipc:[4026532320]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 mnt -> mnt:[4026532317]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 net -> net:[4026532176]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 pid -> pid:[4026532321]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 user -> user:[4026531837]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 uts -> uts:[4026532319]

$ ls -al /proc/$$/ns
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 ipc -> ipc:[4026531839]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 mnt -> mnt:[4026531840]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 net -> net:[4026531956]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 pid -> pid:[4026531836]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 user -> user:[4026531837]
lrwxrwxrwx. 1 root root 0 17 janv. 11:21 uts -> uts:[4026531838]

# Des namespaces différents sont bien utilisés
```

* bonus : modification du stage1 de rkt pour lancer des conteneurs dans VMs KVM.
    * Pas de détails ici, [la doc](https://coreos.com/rkt/docs/latest/running-kvm-stage1.html) est très complète à ce sujet
    *  On va profiter des capacités d'isolation des VMs pour faire nos conteneurs. Les outils liés (comme KVM) sont optimisés pour la conteneurisation : très peu de pertes en perfs !
    * Depuis peu, la techno KVM utilisée est celle développée par Intel pour les Clear Containers, [désormais intégrés au projet Kata](https://clearlinux.org/containers)
    
# Docker Basics
## 1. Basic configuration

* installation et démarrage de Docker

* ajout des dépôts (doc officielle)
```
$ yum-config-manager
>     --add-repo
>     https://download.docker.com/linux/centos/docker-ce.repo
```
* installation du paquet `docker-ce`
* démarrage et activation du service systemd : `systemctl start docker && systemctl enable docker` 

* pour ajouter l'utilisateur courant au groupe `docker` : `usermod -aG docker $(whoami)`

* cette restriction (root ou groupe docker) est apposé sur le socket qui nous sert à communiquer avec le démon Docker :
```
[root@first ~]# ls -al /var/run/docker.sock 
srw-rw----. 1 root docker 0 17 janv. 12:02 /var/run/docker.sock
```
* pour rappel : user/client (docker) <--> socket <--> application/serveur (dockerd)

* modification du répertoire de travail de Docker pour pointer vers `/data`, et modification du OOM score de `dockerd` :
```
$ mkdir /data

$ cat /etc/docker/daemon.json 
{
	"data-root": "/data",
	"oom-score-adjust": -500
}

$ systemctl restart docker
```

* création d'une deuxième unité systemd de type service pour lancer un deuxième démon docker écoute non pas sur un socket UNIX mais sur un socket TCP : 
```
# création d'un deuxième répertoire de travail
$ mkdir -p /data-tcp`

# création d'un deuxième fichier de conf 
$ cp /etc/docker/daemon.json /etc/docker/daemon-tcp.json`

# changement de l'emplacement du PID file pour éviter les conflits avec le premier 
$ cat /etc/docker/daemon-tcp.json 
{
	"data-root": "/data-tcp",
	"oom-score-adjust": -500,
	"pidfile": "/var/run/docker-tcp.pid"
}

# création d'une deuxième unité systemd
$ cp /usr/lib/systemd/system/docker.service /etc/systemd/system/docker-tcp.service
$ cat /etc/systemd/system/docker-tcp.service
[...]
ExecStart=/usr/bin/dockerd -H tcp://0.0.0.0:4444 --config-file /etc/docker/daemon-tcp.json
[...]

$ systemctl daemon-reload

# ouverture d'un port dans le firewall 
$ firewall-cmd --add-port=4444/tcp --zone=public --permanent
success
$ firewall-cmd --reload
success

# lancement du service
$ systemctl start docker-tcp

$  docker -H tcp://12.12.12.100:4444 ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
# fonctionne aussi depuis la macine hôte :) (12.12.12.100 c'est l'IP locale de la VM)
```

## 2. Basic Operations

* pour lancer un conteneur dont les processus n'appartiendront pas à root, on utilise le flag `-u` de docker `docker run` : 
```
$ docker run -u 9997 -d alpine sleep 999

$ ps -ef | grep sleep
9997      2255  2245  0 12:38 ?        00:00:00 sleep 999
root      2309  1462  0 12:38 pts/0    00:00:00 grep --color=auto sleep
```

* monter le home de l'hôte dans un conteneur alpine
```
$ docker run -it -v /home:/host-home alpine sh
/ # ls /host-home/
it4        toto
```

* créer un serv web NGINX qui sert une page HTML stockée sur l'hôte Docker, accessible depuis le laptop :
```
# création d'un répertoire de travail
$ mkdir -p /srv/TP1/docker/nginx-test/

# création de la page HTML
$  echo "<h1>YOLO</h1>" > /srv/TP1/docker/nginx-test/index.html

# lancement du conteneur 
$ docker run -d -v /srv/TP1/docker/nginx-test/index.html:/var/www/html/index.html -p 3333:80 nginx 

# config firewall 
$ firewall-cmd --add-port=3333/tcp --zone=public --permanent
success
$ firewall-cmd --reload
success

# test depuis la VM 
$ curl localhost:3333
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
[...]
```

Ca marche aussi depuis l'hôte avec un navigateur web en graphique sur l'IP de la VM (http://12.12.12.100:3333 chez moi donc)

## 3. HTTP API

* je vais vous épargner les retours format JSON de mille lignes pour cette correction
* liste des conteneurs :
```
$ curl -X GET --unix-socket /var/run/docker.sock http://localhost/containers/json
```
* liste des images : 
```
curl -X GET --unix-socket /var/run/docker.sock http://localhost/images/json
```

* créer un conteneur puis le démarrer
```
# création
$ curl --unix-socket /var/run/docker.sock -H "Content-Type: application/json"   -d '{"Image": "alpine", "Cmd": ["sleep", "1337"]}'   -X POST http://localhost/containers/create
{"Id":"b5070c30edb4466621fdf0cd34bba6897b46ea8220ea11e916f203479122cb45","Warnings":null}

# démarrage
$ curl --unix-socket /var/run/docker.sock -X POST http://localhost/containers/b5070c30edb4/start

# récupération de son IP 
$ curl --unix-socket /var/run/docker.sock -X GET http://localhost/containers/b5070c30edb4/json | python -m json.tool | grep -i ipaddr$
        "IPAddress": "172.17.0.3",
                "IPAddress": "172.17.0.3",
        "SecondaryIPAddresses": null,
```

# 4. Robust conf
* mettre en place les user-namespaces
```
$ grubby --args="user_namespace.enable=1" --update-kernel="$(grubby --default-kernel)"
$ grubby --args="namespace.unpriv_enable=1" --update-kernel="$(grubby --default-kernel)"
$ reboot
$ sysctl user.max_user_namespaces=15000
# Pour rendre ce dernier changement permanent, on peut créer un fichier dans `/etc/sysctl.d/`
$  echo "user.max_user_namespaces=15000" > /etc/sysctl.d/user-ns.conf

# création d'un user
$ useradd bozo

# création de fichiers subuid et subgid
$ echo "bozo:100000:65536" > /etc/subuid
$ echo "bozo:100000:65536" > /etc/subgid

# modification du ExecStart de l'unité systemd docker.service
$ cat /usr/lib/systemd/system/docker.service | grep ExecStart
ExecStart=/usr/bin/dockerd --userns-remap=bozo

# redémarrage de Docker
$ systemctl daemon-reload
$ systemctl restart docker

# vérification : répertoire /data
$ ls -al /data
[root@first ~]# ls -al /data
total 8
drwx--x--x. 15 root   root    205 17 janv. 13:07 .
dr-xr-xr-x. 19 root   root    252 17 janv. 12:14 ..
drwx------. 14 100000 100000  184 17 janv. 13:07 100000.100000
drwx------.  2 root   root     24 17 janv. 12:07 builder
[...]

# vérification : process
$ docker run -d alpine sleep 9999
e404eb20b7f3b44458d1387044f6ee8405b45a66aead4c8ddf8ee919b54ae119
$ ps -ef | grep sleep
100000    3508  3498  1 13:08 ?        00:00:00 sleep 9999

```

* utilisation de la politique seccomp recommandée par Moby (elle est déjà utilisée par défaut en fait, mais on peut l'expliciter pour la mettre à jour plus tard) : 
```
# création d'un répertoire de travail
$ mkdir -p /srv/TP1/docker/seccomp

# récupération de la politique seccomp
$ curl -SLO https://raw.githubusercontent.com/moby/moby/master/profiles/seccomp/default.json

# ajout dans la configuration 
$ cat /etc/docker/daemon.json 
{
	"data-root": "/data",
	"oom-score-adjust": -500, 
	"seccomp-profile": "/srv/TP1/docker/seccomp/default.json"
}

# systemctl restart docker
```

* configuration de la backend de stockage : direct-lvm mode (voir [doc Docker](https://docs.docker.com/engine/userguide/storagedriver/device-mapper-driver/#configure-direct-lvm-mode-for-production)  pour plus de détails). Après avoir ajouté un nouveau disque à la VM : 
```
# identification du nouveau disque :
$ lsblk
NAME            MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda               8:0    0    8G  0 disk 
├─sda1            8:1    0    1G  0 part /boot
└─sda2            8:2    0    7G  0 part 
  ├─centos-root 253:0    0  6,2G  0 lvm  /
  └─centos-swap 253:1    0  820M  0 lvm  [SWAP]
sdb               8:16   0   10G  0 disk 
sr0              11:0    1 1024M  0 rom 

# sdb n'est pas utilisé, c'est notre disque. On suit la doc Docker pour ce qui est de la config LVM :

$ pvcreate /dev/sdb
$ vgcreate docker /dev/sdb
$ lvcreate --wipesignatures y -n thinpool docker -l 95%VG
$ lvcreate --wipesignatures y -n thinpoolmeta docker -l 1%VG
$ lvconvert -y --zero n -c 512K --thinpool docker/thinpool --poolmetadata docker/thinpoolmeta

$ cat /etc/lvm/profile/docker-thinpool.profile
activation {
  thin_pool_autoextend_threshold=80
  thin_pool_autoextend_percent=20
}

$ lvchange --metadataprofile docker-thinpool docker/thinpool
$ lvs -o+seg_monitor
$ rm -rf /data /var/lib/docker/

$ cat /etc/docker/daemon.json 
{
	"data-root": "/data",
	"oom-score-adjust": -500, 
	"seccomp-profile": "/srv/TP1/docker/seccomp/default.json",
        "storage-driver": "devicemapper",
        "storage-opts": [
        "dm.thinpooldev=/dev/mapper/docker-thinpool",
        "dm.use_deferred_removal=true",
        "dm.use_deferred_deletion=true"
        ]
}

# vérification
$ sudo systemctl start docker
$ docker info
[...]
Storage Driver: devicemapper
 Pool Name: docker-thinpool
 Pool Blocksize: 524.3kB
 Base Device Size: 10.74GB
 Backing Filesystem: xfs
 Udev Sync Supported: true
 Data Space Used: 20.45MB
 Data Space Total: 10.2GB
 Data Space Available: 10.18GB
 Metadata Space Used: 49.15kB
 Metadata Space Total: 104.9MB
 Metadata Space Available: 104.8MB
 Thin Pool Minimum Free Space: 1.019GB
 Deferred Removal Enabled: true
 Deferred Deletion Enabled: true
 Deferred Deleted Device Count: 0
 [...]

# j'ai que 10Go de libre

# test 
$ docker run --storage-opt size=20G -it alpine sh
/ # df -h
Filesystem                Size      Used Available Use% Mounted on
/dev/mapper/docker-253:0-8832037-7cac9a59afc875c4a38c2b1220c7c5894c1f3c7e0deb45f34fe4a13ea260256e
                         20.0G     37.6M     20.0G   0% /
[...]
# dans le conteneur y'a 20Go : thin provisionning !
```

Ca permet de faire du thin provisionning, avoir des volumes dédiés au stockage Docker, faire des snapshots LVM, agrandir à chaud la place disponible, entre autres.

* beaucoup d'options de `docker run` sont liées à la sécu. Notamment : 
    * limitation accès disque/réseau/RAM/CPU très fine
    * `-u` pour lancer des process non-root
    * `--ulimit` pour changer le ulimit par défaut du conteneur
    * `--oom-score-adj` poru changer le OOM score des conteneurs (pas du démon)

# 5. Compose
* installer `docker-compose`
```
$ curl -L https://github.com/docker/compose/releases/download/1.18.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose

$ chmod +x /usr/local/bin/docker-compose
```

# 6. GUI ? 

* déploiement de Portainer
```
$ docker run -d -p 9000:9000 --restart always -v /var/run/docker.sock:/var/run/docker.sock -v /opt/portainer:/data portainer/portainer
```

* création d'un swarm 
```
# Sur un premier noeud
$ docker swarm init --advertise-addr 12.12.12.100
```
```
# sur le deuxième noeud, utiliser la commande récupérée au moment du `swarm init`
$ docker swarm join --token SWMTKN-1-4scgbxcldszt7y4r3pveja4jrozvj9vlsvekl1dfzix2ihxgwf-5xy5is1eulxsfs06u4gv04fcd 12.12.12.100:2377
```