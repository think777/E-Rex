//Load Clubs
LOAD CSV WITH HEADERS FROM "file:///ClubsNeo4j.csv" AS row
CREATE (n:Club)
SET n = row

//Load Events
LOAD CSV WITH HEADERS FROM "file:///EventsSample1000Neo4j.csv" AS row
CREATE (n:Event)
SET n = row

//Load Students
LOAD CSV WITH HEADERS FROM "file:///StudentsNeo4j.csv" AS row
CREATE (n:Student)
SET n = row

//Convert string to Neo4j list
MATCH (c:Student)
WITH c, split(c.ClubName, ',') AS membersList
SET c.ClubName = membersList

//Connect Clubs and Events
MATCH (p:Event),(c:Club)
WHERE p.ClubId = c.ClubId
MERGE (p)-[:HOSTED_BY]-(c)

CREATE INDEX FOR (c:Student) ON (c.StudentId)

CREATE INDEX FOR (c:Event) ON (c.EventId)

CREATE INDEX FOR (c:Club) ON (c.ClubId)