# tinyproxy
A Flask based proxy for interfacing to a Neo4j server in a Docker container

The [Neo4j](https://neo4j.com/) graph databases exposes a HTTP server on port 7474. When a browser connects to
this port it is redirected to `/browser` and a browser based shell (written in 
[preact](https://github.com/developit/preact)) is loaded. This then communicates with the database using the *bolt*
protocol.

When running Neo4j from a Docker container, two ports need to be exposed: the HTTP port (7474 by default) and
the Bolt port (7687 by default). The browser shell is loaded (and loads components) on the HTTP port and then
it connects to the Bolt port. As soon as the browser loads it makes a request back to the HTTP port to get 
configuration. If the Docker container is inspected (using `docker port`) to list the internal / external
port mappings, the browser request for configuration can be intercepted and correct configuration to
use the Docker container returned.

This proxy is a research project towards creating a viable Neo4j 3.2.0 Interactive Environment for [Galaxy](https://galaxyproject.org/).
