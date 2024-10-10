# Tips G5k

- To execute a script on a given list of servers (chifflot) during 4 hours max: 

```
oarsub -l {"host in ('chifflot-1.lille.grid5000.fr','chifflot-4.lille.grid5000.fr','chifflot-5.lille.grid5000.fr')"}/host=1,walltime=4 ./my_script.sh
```

- To check usage policy: 

```
usagepolicycheck -t
```

- To install docker : 

```
g5k-setup-docker -t
``` 

- To check reservations at Lille site (with authentification): 

https://intranet.grid5000.fr/oar/Lille/monika.cgi
