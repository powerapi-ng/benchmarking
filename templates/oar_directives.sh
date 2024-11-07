#OAR -q {{ queue_type }}
#OAR -p {{ node_uid }}
#OAR -t night
#OAR -l host=1
#OAR -l walltime={{ walltime }}
    {%- if exotic_node -%}
#OAR -t exotic_node
    {% endif %}
