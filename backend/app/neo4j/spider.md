- If a node can be reached through multiple paths, indicates stronger relationship
- As the distance increases, relationship becomes weaker
    - Distance here is not the number of edges traversed, but is the summation of the weighted edges traversed
        - Higher the weights, stronger the relationship between nodes
- We start from a student node, and traverse its neighbourhood. Initially(1-hop), we only find club-student and event-student edges.

Different phases:
1) Construct: inital node and edge additions
2) Weave: assign weights to edges(paths), and build bridges
3) Crawl: traverse the graph to find preferred events
4) AssessChanges: trace the dependencies and re-weight