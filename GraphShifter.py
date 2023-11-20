from neo4j import GraphDatabase,exceptions
import csv
#from backend.app.neo4j.helper import create_relationships_with_clubs,create_relationships_with_events

uri = "bolt://localhost:7687"
username = 'neo4j'
password = 'testtest'

driver=GraphDatabase.driver(uri,auth=(username,password))
session=driver.session()

#Export nodes to csv file(stored in import folder)
query="""
MATCH (startNode:Student {StudentId: '1'})
MATCH (startNode)-[*1..3]-(e:Event)
WITH COLLECT(DISTINCT e) as Events
CALL apoc.export.csv.data(Events,[],'EventNodes.csv', {})
YIELD file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
RETURN file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
"""
#result=session.run(query)

query="""
MATCH (startNode:Student {StudentId: '1'})
MATCH (startNode)-[*1..3]-(e:Club)
WITH COLLECT(DISTINCT e) as Clubs
CALL apoc.export.csv.data(Clubs,[],'ClubNodes.csv', {})
YIELD file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
RETURN file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
"""
#result=session.run(query)

query="""
MATCH (startNode:Student {StudentId: '1'})
MATCH (startNode)-[*1..3]-(e:Student)
WITH COLLECT(DISTINCT e) as Students
CALL apoc.export.csv.data(Students,[],'StudentNodes.csv', {})
YIELD file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
RETURN file, source, format, nodes, relationships, properties, time, rows, batchSize, batches, done, data
"""
#result=session.run(query)

query="""MATCH (startNode:Student {StudentId: '1'})
MATCH path=(startNode)-[*1..3]-(neighbor)
UNWIND relationships(path) AS rel
RETURN rel,nodes(path)"""

#result=session.run(query)
'''
with open('relationships.csv','w',newline='') as csvfile:
    csvwriter=csv.writer(csvfile)
    # Write the header row
    csvwriter.writerow([':START_ID', ':END_ID', ':TYPE', 'rating'])

    for record in result:
        startNodeId=record["rel"].nodes[0].element_id.split(':')[-1]
        endNodeId=record["rel"].nodes[1].element_id.split(':')[-1]
        csvwriter.writerow([startNodeId,endNodeId,record["rel"].type,record["rel"]["rating"]])
'''

def create_relationships_with_clubs(session, student_node):
    # Get the list of club names from the Student node
    club_names = student_node["ClubName"]
    # Loop through each club name and create relationships
    for club_name in club_names:
        club_name=club_name.split('"')[1].strip()
        # Create a relationship between the Student node and the Club node
        try:
                session.run(
                "MATCH (s:Student {StudentId: $student_id}), (c:Club {Club: $club_name}) "
                "MERGE (s)-[:MEMBER_OF]-(c)",
                student_id=student_node["StudentId"].strip(),
                club_name=club_name
                )
        except exceptions.Neo4jError as e:
                print("Neo4j error:", e)

def create_relationships_with_events(session, student_node):
    # Get the list of club names from the Student node
    event_ids = student_node["EventId"]
    event_ids=event_ids[1:-1].split(',')
    # Loop through each club name and create relationships
    for event_id in event_ids:
        # Create a relationship between the Student node and the Event node
        result=session.run(
            "MATCH (s:Student {StudentId: $student_id}), (e:Event {EventId: $event_id}) "
            "MERGE (s)-[:DIRECT{rating:e.EventRating}]-(e) "
            "MERGE (s)-[:INDIRECT]-(e)",
            student_id=student_node["StudentId"].strip(),
            event_id=event_id.strip()
        )

# Retrieve all Student nodes
student_nodes = session.run("MATCH (s:Student) RETURN s")
# Loop through each Student node and create relationships with clubs
for record in student_nodes:
        student_node = record["s"]
        create_relationships_with_clubs(session, student_node)
        #create_relationships_with_events(session, student_node)