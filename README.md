# B3 - CT 

## Notation

Petit script pour voir vos notes. 

A lancer direct si vous avez Python ou avec la version conteneurisée :)


* **avec Python**
```
$ cd notation/
$ ./notes.py -h
usage: notes.py [-h] [-g GROUP_NUMBER] [-a] [-s]

optional arguments:
  -h, --help       show this help message and exit
  -g GROUP_NUMBER  number of group you want to get the notes of
  -a               print all groups and general average
  -s               print some stats
```

* **version conteneurisée**
```
$ cd notation/
$ docker build -t notes . 
$ docker run notes
usage: notes.py [-h] [-g GROUP_NUMBER] [-a] [-s]

optional arguments:
  -h, --help       show this help message and exit
  -g GROUP_NUMBER  number of group you want to get the notes of
  -a               print all groups and general average
  -s               print some stats

$ docker run notes -g 1
```
