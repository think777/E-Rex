from neo4j import GraphDatabase,exceptions
import json
import random

def getSecret(jsonFile,keyList):
    try:
        with open(jsonFile) as f:
            data=json.load(f)
            temp=data
            for key in keyList:
                temp=temp[key]
            return temp
    except Exception as e:
        print("Error: ",e)

def create_relationships_with_clubs(session, student_node):
    # Get the list of club names from the Student node
    club_names = student_node["ClubName"]
    # Loop through each club name and create relationships
    for club_name in club_names:
        club_name=club_name.strip()
        # Create a relationship between the Student node and the Club node
        session.run(
            "MATCH (s:Student {StudentId: $student_id}), (c:Club {Club: $club_name}) "
            "MERGE (s)-[:MEMBER_OF]-(c)",
            student_id=student_node["StudentId"].strip(),
            club_name=club_name
        )

def create_relationships_with_events(session, student_node):
    # Get the list of club names from the Student node
    event_ids = student_node["EventId"]
    event_ids=event_ids[1:-1].split(',')
    # Loop through each club name and create relationships
    for event_id in event_ids:
        # Create a relationship between the Student node and the Club node
        result=session.run(
            "MATCH (s:Student {StudentId: $student_id}), (c:Event {EventId: $event_id}) "
            "MERGE (s)-[:DIRECT]-(c)",
            student_id=student_node["StudentId"].strip(),
            event_id=event_id.strip()
        )

def returnMetapaths(session,studentName,metapath):
    query=f"""
                MATCH (n:Student)
                WHERE TRIM(n.Name)=$studentName
                WITH n as source
                MATCH path= {metapath}
                RETURN path
            """
    result=session.run(query,studentName=studentName)
    paths=[]
    for record in result:
        paths.append(record['path'])
    return paths

def compareEvents(session,event1Id,event2Id,store):
    #Get Event nodes
    result=session.run("MATCH (n:Event) "
                       "WHERE n.EventId IN [$event1Id,$event2Id] "
                       "RETURN n",
                       event1Id=event1Id,
                       event2Id=event2Id)
    events=[]
    for record in result:
        events.append(record['n'])
    #Compare events
    score=1 if events[0]['ClubId']==events[1]['ClubId'] else 0  #Check if they are hosted by same club
    #Find degrees of both events(popularity)
    temp=[]
    result=session.run("MATCH (e:Event)-[:DIRECT]-(:Student) "
                       "WHERE e.EventId=$event1Id "
                       "RETURN COUNT(e)",
                       event1Id=event1Id)
    temp.append(float(result.single().value()))
    result=session.run("MATCH (e:Event)-[:DIRECT]-(:Student) "
                       "WHERE e.EventId=$event2Id "
                       "RETURN COUNT(e)",
                       event2Id=event2Id)
    temp.append(float(result.single().value()))
    score+=1 if temp[0]==temp[1] else 1/abs(temp[0]-temp[1])    #Find diff. in popularity
    #FIXME EventRating NULL for some Events
    temp=abs(float(events[0]['EventRating'])-float(events[1]['EventRating'])) #Find out diff. in avg. rating
    score+=1 if temp<1 else 1/temp  #TODO Factor in number of people who have given rating
    temp=abs(int(events[0]['PrizePool'])-int(events[1]['PrizePool'])) #Find out diff. in prize pool
    score+=1 if temp==0 else 1/temp
    #TODO Compare EventDate with context
    #Find similarity in EventType
    temp=0
    for type1 in events[0]['EventType']:
        for type2 in events[1]['EventType']:
            if type1==type2:
                temp+=1
    temp1=set(events[0]['EventType'])
    temp2=set(events[1]['EventType'])
    score+=len(temp1 & temp2)/len(temp1 | temp2)    #Ration of common event types to all event types
    score/=5  #Normalize wrt number of event properties compared
    #Store the calculated similarity score in the relationship
    if store:
        session.run("MATCH (e1:Event {EventId:$event1Id}),(e2:Event {EventId:$event2Id}) "
                    "MERGE (e1)-[:EVENT_SIMILARITY{score:$score}]-(e2) "
                    "RETURN e1,e2",
                    event1Id=event1Id,
                    event2Id=event2Id,
                    score=score)
    return score

def analyzeNeighbourhood(session,studentName):
    studentName=studentName.strip()
    result=session.run("MATCH (n:Student) "
                     "WHERE TRIM(n.Name)=$studentName "
                     "RETURN n",
                     studentName=studentName)
    root=result.single().value()
    metapaths={'meta_SCE':'(source)-[:MEMBER_OF]-(:Club)-[:HOSTED_BY]-(:Event)',
               'meta_SCS':'(source)-[:MEMBER_OF]-(:Club)-[:MEMBER_OF]-(:Student)',
               'meta_SEC':'(source)-[:DIRECT]-(:Event)-[:HOSTED_BY]-(:Club)',
               'meta_SES':'(source)-[:DIRECT]-(:Event)-[:DIRECT]-(:Student)'}
    for key in metapaths.keys():
        paths=returnMetapaths(session,studentName,metapaths[key])
        query=f"""
            MATCH (n:Student)
            WHERE n.StudentId=$studentId
            SET n.{key}='{len(paths)}'
            RETURN n
            """
        session.run(query,studentId=root['StudentId'])
    '''session.run("MATCH (n:Student) "
                        "WHERE TRIM(n.Name)=$studentName "
                        "WITH n as source "
                        "MATCH (source)-[r*1..2]-(neighbour) "
                        "RETURN source,r,neighbour",
                        studentName=studentName)
    # Iterate through the records and print nodes and relationships
    for record in neighbourhoodSubGraph:
        source_node = record["source"]
        relationships = record["r"]
        neighbor_node = record["neighbour"]
        
        print(f"Source Node: {source_node}")
        
        for relationship in relationships:
            print(f"Relationship: {relationship}")
        
        print(f"Neighbor Node: {neighbor_node}")
    return neighbourhoodSubGraph'''

def main():
    try:
        # Define your Neo4j connection parameters
        uri = "bolt://localhost:7687"
        username = getSecret('secrets.json',['neo4jdb','username'])
        password = getSecret('secrets.json',['neo4jdb','password'])

        # Create a session
        with GraphDatabase.driver(uri, auth=(username, password)) as driver:
            with driver.session() as session:
                #MODULARISE API format for diff. funcs.
                '''# Retrieve all Student nodes
                student_nodes = session.run("MATCH (s:Student) RETURN s")

                # Loop through each Student node and create relationships with clubs
                for record in student_nodes:
                    student_node = record["s"]
                    create_relationships_with_clubs(session, student_node)
                    #create_relationships_with_events(session, student_node)'''
                '''
                #MODULARISE Seperate func. to fill missing vals
                result=session.run("MATCH (n:Event) "
                                   "WHERE n.EventRating IS NULL "
                                   "RETURN n.EventId")
                for record in result:
                    eventId=record["n.EventId"]
                    temp=round(random.uniform(4.0,10.0),2)
                    session.run("MATCH (n:Event) "
                                "WHERE n.EventId=$eventId "
                                "SET n.EventRating=$randVal "
                                "RETURN n",
                                eventId=eventId,
                                randVal=temp)
                '''
                print(compareEvents(session,'6781','7856',True))

    except exceptions.Neo4jError as e:
        print("Neo4j error:", e)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()