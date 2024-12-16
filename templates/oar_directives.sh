#OAR -q {{ queue_type }}
#OAR -p {{ node_uid }}
#OAR -l host=1,walltime={{ walltime }}
{% if exotic_node %}
#OAR -t exotic
{% endif %}
