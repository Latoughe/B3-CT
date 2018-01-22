# B3 - Conteneurisation 

**RAPPELS** :    

* désactiver SELinux
* laisser **activé** le firewall et le configurer si besoin
* inspirez-vous du TP précédent pour certains détails (install + conf Docker)

## Part 1 : Gitlab
Ici, seront déployés, sur une nouvelle VM :  

* un gitlab-ce 
* un gitlab-runner
* un démon Docker
* un registry Docker

Le but va être de monter une pipeline de CI/CD Gitlab. Un morceau de code vous sera fourni, il devra être hébergé par Gitlab, testé lors des commits, puis déployé sur un serveur de "staging". 

**1. Ajout d'un disque** 

* ajouter un disque à la machine (30Go)
* utiliser LVM : ajouter ce disque à un volume group nouvellement créé, et s'en servir pour monter une partition `/data` de 15 Go
* cette partition `/data` stockera... les données de vos application
    
**2. Installer Docker**

* suivre la doc officielle
* utiliser comme répertoire de données `/data/docker`

**3. Installer gitlab-ce**
On va utiliser l'installation "omnibus" de Gitlab. N'hésitez pas à vous référer à la doc officielle. 
    
```
sudo firewall-cmd --permanent --add-service=http
sudo systemctl reload firewalld
sudo yum install postfix
sudo systemctl enable postfix
sudo systemctl start postfix
curl https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.rpm.sh | sudo bash
sudo EXTERNAL_URL="http://<HOSTNAME>" yum install -y gitlab-ce
```

* une fois terminé, il vous faudra activer le TLS
    * vous pouvez générer une paire de clé avec la commande : `openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout server.key -out server.crt`
    * déplacer le certificat dans `/etc/gitlab/ssl/<HOSTNAME>.crt`
    * déplacer la clé dans `/etc/gitlab/ssl/<HOSTNAME>.key`
    * modifier le fichier `/etc/gitlab/gitlab.rb` :
        * `external_url 'https://<HOSTNAME>'`
    * redémarrer gitlab complètement avec `gitlab-ctl reconfigure`
    * oubliez pas de reconfigurer le firewall !
* vous devrez pouvoir vous connecter sur `https://<HOSTNAME>`

* créer un projet de test sur l'interface Gitlab, et récupérer le dépôt Git en local

* on va aussi activer le registre Docker
    * modifier le fichier `/etc/gitlab/gitlab.rb` :
        * `registry_external_url 'https://<HOSTNAME>:<PORT>'`
    * redémarrer gitlab complètement avec `gitlab-ctl reconfigure`
* vous devriez pouvoir avoir accès au registre dans votre projet (sur l'interface web)
* et vous devriez pouvoir vous logger avec `docker login <HOSTNAME>:<PORT>`
    * sauf que votre registe est 'insecure' : le certificat est auto-signé
    * pour cela, il faudra copier le  certificat dans `/etc/docker/certs.d/<HOST>/ca.crt` (créer le répertoire s'il n'existe pas) afin de faire confiance au certificat
    * le nom du dossier <HOST> *est important* (doit porter le hostname du registre)
    * le nom du certificat `ca.crt` est lui aussi *obligatoire*

* push une image sur l'espace du registre dédié à ce projet
    * le nom de l'image doit se conformer à une syntaxe précise, par exemple, pour push une image alpine
```
# On récupère une image alpine sur le Hub
docker pull alpine

# On la retag en suivant la convention de nommage (obligatoire)
docker tag alpine <REGISTRY_URL>:<PORT>/<GITLAB_USER>/<GITLAB_REPO>/<IMAGE>:<TAG>

# Par exemple
docker tag alpine gitlab.b3.ingesup:9999/root/test-project/alpine:mine

# On se log à notre registre
docker login <HOSTNAME>:<PORT>
# Par exemple
docker login gitlab.b3.ingesup:9999

# On peut push 
docker push gitlab.b3.ingesup:9999/root/test-project/alpine:mine 
```

* (optionnel) Mettre en place un contrôle de syntaxe des fichiers Dockerfile et docker-compose.yml qui sont poussés sur le dépôt

**4. Mettre en place un build automatisé**

* installer un runner (il lancera vos tests)
    * se référer à [cette doc](https://docs.gitlab.com/runner/install/linux-repository.html)
* enregistrer le runner pour votre projet
    * vous trouverez le token sur l'interface graphique, dans votre projet, `Settings > CI/CD > Runner Settings`
```
sudo gitlab-runner register \
  --url "https://<HOSTNAME>/" \
  --registration-token "PROJECT_REGISTRATION_TOKEN" \
  --description "docker-runner" \
  --executor "docker" \
  --docker-image docker:latest
```
* un fichier a été généré dans `/etc/gilab-runner/config.toml`
    * éditer le
    * dans la clause [[runners.docker]] ajoutez les lignes :
        * `volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]`
        * `extra_hosts = ["<HOSTNAME>:<IP>"]`
        
* créer un fichier `.gitlab-ci.yml` à la racine du dépôt de votre projet
    * un build très simpliste peut ressembler à :
```
image: 
  name: debian:8-slim

sleepytest:
  script:
  - ls
  - whoami
  - df -h
  - /bin/sleep 5
```
* mettre en place le build simpliste mentionné plus haut

* mettre en place le build d'un Dockerfile
    * l'image utilisé pour le build devra posséder les commandes docker. A des fins de tests, utilisez l'image `docker:latest`
    * cette image lancera le build d'un Dockerfile avec python3 et le binaire curl dedans (pour les tests)
    * le test devra exécuter la commande `python -m http.server 8000` (la commande lance un serveur web sur le port 8000)
    * tester le bon fonctionnement du serveur web avec `curl`
    * si le `docker build` passe,  un `docker login` et un `docker push` devront être réalisés pour pousser l'image sur le registre

## Part 2 : Docker swarm

* utiliser le package fourni pour construire un `docker-compose.yml`
    * même code que la dernière fois (ou presque)
    * utiliser la commande `docker-compose up` avec l'option `--scale` pour faire pop trois, quatre ou plus de conteneur `app`
    * le loadbalancing est automatiquement effectué par NGINX, expliquer cela
    
* créer un swarm avec 3 noeuds
    * sur chaque noeud, Docker devra être installé en version ce-edge
    * modifier la configuration du démon pour utiliser 
        * `metrics-addr: 0.0.0.0:9323` afin de récolter des métriques sur le swarm plus tard (expérimental encore)
        * `experimental: true` à true
    * faites attention à votre firewall (voir [ici](https://docs.docker.com/engine/swarm/swarm-tutorial/#the-ip-address-of-the-manager-machine) pour plus de renseignements sur les ports à ouvrir)

* déployer un registre Docker, utilisable depuis vos 3 noeuds, et du TLS (certificats auto-signés)
    * depuis les clients, il faudra copier le  certificat dans `/etc/docker/certs.d/<HOST>.b3.ingesup/ca.crt` (créer le répertoire s'il n'existe pas) afin de faire confiance au certificat

* adapter le compose pour pouvoir le déployer sur le swarm
    * vous aurez besoin des clauses comme
```
deploy:
  mode: replicated
  replicas: 5
  labels: [THIS_IS=THE_APP]
  placement:
    constraints: [node.role == worker]
```

* lancer un Portainer pour piloter le swarm (en tant que service swarm, pas juste un docker run :) )

* utiliser Weave Cloud pour monitorer votre déploiement Swarm

## Part 3 (bonus) : Kubernetes

* **caractéristiques**
    * orchestration de conteneurs (comme Swarm)
    * projet de Google
    * réputé très robuste
    * profondément ancré dans le monde de la conteneurisation/cloud/microservices

Ici est décrite une installation extrêmement simplifiée, sans détails, visant juste à mettre en place un petit cluster Kubernetes (pas très très sécurisé, mais fonctionnel :) ).

On va l'installer avec `kubeadm`. 
Préparez deux machines : 
	
* la première avec un petit 2/3Go de RAM ça fait pas de mal, et 2 coeurs proc
* centOS7
* swap désactivée (`swapoff` et/ou `/etc/fstab`)
* docker installé
    * le démon utilise le driver cgroup `cgroupfs` (`--exec-opt native.cgroupdriver=cgroupfs` sur la ligne `dockerd`)
* les éléments nécessaire à Kubernetes installés, suivre la doc [ici](https://kubernetes.io/docs/setup/independent/install-kubeadm/)
*   * le kubelet utilise aussi le driver cgroup `cgroupfs` (dans le fichier `/etc/systemd/system/kubelet.service.d/10-kubeadm.conf`)
    * ces deux configs permettent d'évite des problèmes plus tard. L'idée est surtout de mettre le même driver des deux côtés (`docker` et `kubelet`). `cgroupfs` sera celui qui vous posera le moins de soucis de configuration.

* lisez ce qu'il y a en dessous **d'abord** puis suivre la doc [ici](https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/)
    * on va utiliser Calico comme driver réseau. Donc pour l'initialisation du cluster (ça peut prendre un p'tit moment)   avec `kubeadm init` utilisez : 
```
kubeadm init --pod-network-cidr=192.168.0.0/16 --apiserver-advertise-address <VM_IP>
```
* après l'init, attendez que les pods soient en état de marche avant de dérouler la documentation (seul les DNS doivent restés éteints)
   * une fois le cluster mis en place (quand vous faites un `kubectl get pods --all-namespace` tout le monde devrait être OK) déployez le dashboard Kubernetes avec :
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/recommended/kubernetes-dashboard.yaml
```
* pour que vous puissiez bypass le login (c'est sale, mais on veut juste que ça marche :) ) : 
    
    
```
cat <<EOF | kubectl create -f -
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: kubernetes-dashboard
  labels:
    k8s-app: kubernetes-dashboard
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: kubernetes-dashboard
  namespace: kube-system
EOF
```
* pour pouvoir y accéder depuis un navigateur de votre hôte : 
```
kubectl proxy --address <VM_IP> --accept-hosts='.*'
```
* go sur `http://<VM_IP>:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/`
* essayez de déployer un service de test (en plus du dashboard)
* on peut monter une stack avec un Heapster(+InfluxDB +Grafana) pour avoir des métriques dans le dashboard Kubernetes, ou aussi un Weave, ou du Prometheus !
