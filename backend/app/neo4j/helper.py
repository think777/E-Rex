from neo4j import GraphDatabase,exceptions
import json
import random
import math
import ast
import ast

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
        # Create a relationship between the Student node and the Event node
        result=session.run(
            "MATCH (s:Student {StudentId: $student_id}), (e:Event {EventId: $event_id}) "
            "MERGE (s)-[:DIRECT{rating:e.EventRating}]-(e) ",
            "MERGE (s)-[:INDIRECT]-(e) ",
            student_id=student_node["StudentId"].strip(),
            event_id=event_id.strip()
        )
        #CHECK

def returnMetapaths(session,studentId,metapath):
    query=f"""
        MATCH (s:Student {{StudentId:$studentId}})
        WITH s as source
        MATCH path= {metapath}
        RETURN path
        """
    result=session.run(query,studentId=studentId)
    paths=[]
    for record in result:
        paths.append(record['path'])
    return paths

#OPTIMIZE Add model to calculate agg. score
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
    if(len(events)!=2):
        return None
    #Compare events
    #Compare node features
    score=1 if events[0]['ClubId']==events[1]['ClubId'] else 0  #Check if they are hosted by same club
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
    score+=len(temp1 & temp2)/len(temp1 | temp2)    #Ratio of common event types to all event types
    #Compare network features
    #Find degrees of both events(popularity)
    rel=[{'r':[],'s':{}},{'r':[],'s':{}}]
    #OPTIMIZE Reduce number of queries
    #Get the relationships between students and events
    result=session.run("MATCH (e:Event)-[r:DIRECT]-(s:Student) "
                       "WHERE e.EventId=$event1Id "
                       "RETURN r,s",
                       event1Id=event1Id)
    '''
    PROTOTYPE rel
    {
        #Event1
        [
            'r':{
                [Relationship1,Relationship2,...]
            },
            's':{
                CommonStudentId1:RatingEvent1,
                ...
            }
        ],
        #Event2
        [
            'r':{
                [Relationship1,Relationship2,...]
            },
            's':{
                CommonStudentId1:Rating1Event2,
                ...
            }
        ]
    }
    Relationship: Student-ATTENDED->Event
    '''
    for record in result:
        rel[0]['r'].append(record["r"])
        rel[0]['s'][record["r"].nodes[0]['StudentId']]=float(record["r"]['rating'])   #Store the student IDs as keys and their ratings as vals. in dict.
    result=session.run("MATCH (e:Event)-[r:DIRECT]-(s:Student) "
                       "WHERE e.EventId=$event2Id "
                       "RETURN r,s",
                       event2Id=event2Id)
    for record in result:
        rel[1]['r'].append(record["r"])
        rel[1]['s'][record["r"].nodes[0]['StudentId']]=float(record["r"]['rating'])
    #Convert the list of student IDs(keys of dict.) to set of student IDs to carry out UNION and INTERSECTION ops.
    temp1=set(rel[0]['s'].keys())
    temp2=set(rel[1]['s'].keys())
    commonStudents=temp1 & temp2
    temp=0
    '''
    Find out the difference in how each student who has attended both the events has rated them
    1) Both events are liked by students: events are similar
    2) Both events are disliked by students: events are similar
    3) One event is liked and one disliked: events are dissimilar
    '''
    #CHECK
    for student in commonStudents:
        temp+=1 if rel[0]['s'][student]==rel[1]['s'][student] else 1/abs(rel[0]['s'][student]-rel[1]['s'][student])
    score+=temp/len(temp1 | temp2)  #Normalize wrt the number of students who has attended either event
    temp1=len(rel[0]['r'])
    temp2=len(rel[1]['r'])
    score+=1 if temp1==temp2 else 1/abs(temp1-temp2)    #Find diff. in popularity
    #FIXME EventRating NULL for some Events
    temp=abs(float(events[0]['EventRating'])-float(events[1]['EventRating'])) #Find out diff. in avg. rating
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

#OPTIMIZE Add model to calculate agg. score
def compareStudents(session,studentId1,studentId2,store):
    score=0
    query=f"""
        MATCH (s1:Student {{StudentId:$studentId1}}),(s2:Student {{StudentId:$studentId2}})
        RETURN s1,s2
        """
    result=session.run(query,studentId1=studentId1,studentId2=studentId2)
    students=result.single()
    if(students is None):
        return None
    #Compare node features
    score+=1 if students["s1"]["Branch"]==students["s2"]["Branch"] else 0   #Check whether students belong to same branch
    score+=1 if students["s1"]["Semester"]==students["s2"]["Semester"] else 0   #Check whether students belong to the same semester
    temp1=float(students["s1"]["CGPA"])
    temp2=float(students["s2"]["CGPA"])
    score+=1 if round(temp1,1)==round(temp2,1) else 1/abs(temp1-temp2)  #Find similarity in students' CGPAs
    #Compare network features
    temp1=set(students["s1"]["ClubName"])
    temp2=set(students["s2"]["ClubName"])
    score+=len(temp1 & temp2)/len(temp1 | temp2)    #Find the ratio of common clubs to all clubs they are members of
    #Find common events attended by student1 and student2
    query=f"""
        MATCH (s1:Student {{StudentId:$studentId1}})-[r1:DIRECT]-(:Event)-[r2:DIRECT]-(s2:Student {{StudentId:$studentId2}})
        RETURN r1,r2
    """
    result=session.run(query,studentId1=studentId1,studentId2=studentId2)
    temp=0
    '''
    Find out the difference in how each student who has attended both the events has rated them
    1) An event is liked by both students: students' interests are similar
    2) An event is disliked by both students: students' interests are similar
    3) An event is liked by one student and disliked by the other: students' interests are dissimilar
    '''
    for record in result:
        temp+=1 if record["r1"]["rating"]==record["r2"]["rating"] else 1/abs(record["r1"]["rating"]-record["r2"]["rating"])
    score+=temp/len(set(students["s1"]["EventId"]) | set(students["s2"]["EventId"]))
    score/=5    #Normalize score wrt number of properties considered
    if(store):
        query="""
            MATCH (s1:Student {StudentId:$studentId1}), (s2:Student {StudentId:$studentId2})
            MERGE (s1)-[:STUDENT_SIMILARITY{score:$score}]-(s2)
        """
        session.run(query,studentId1=studentId1,studentId2=studentId2,score=score)
    return score

def calculate_weighted_similarity(student_interests, club_description):
    student_scores = dict(student_interests)
    club_scores = dict(club_description)
    all_topics = set(student_scores.keys()).union(club_scores.keys())
    weighted_sum = sum(student_scores.get(topic, 0) * club_scores.get(topic, 0) for topic in all_topics)
    magnitude_student = sum(score ** 2 for score in student_scores.values()) ** 0.5
    magnitude_club = sum(score ** 2 for score in club_scores.values()) ** 0.5
    if magnitude_student == 0 or magnitude_club == 0:
        return 0
    similarity = weighted_sum / (magnitude_student * magnitude_club)
    return similarity

def studentEventSim(session,studentId,eventId,**kwargs):
    query="""
    MATCH (s:Student {StudentId:$studentId}),(e:Event {EventId:$eventId})
    RETURN s,e
    """
    result=session.run(query,studentId=studentId,eventId=eventId)
    temp=result.single()
    if temp is None:
        return None
    studNode,eventNode=temp["s"],temp["e"]
    query="""
    MATCH (c:Club {ClubId:$clubId})
    RETURN c.Club as club
    """
    result=session.run(query,clubId=eventNode["ClubId"]).single()
    score=0
    #FIXME Remove this condition later
    if result:
        club=result["club"].strip()
        #club=f"[\"{club}\"]"
        #Check if student is a member of the club that hosted(/is hosting) the event
        temp=0
        for x in studNode["ClubName"]:
            if x[2:-2].strip()==club:
                temp=1
                break
        score+=temp
    query="""
    MATCH (s:Student {StudentId:$studentId})-[r:DIRECT|INDIRECT]-(e:Event {EventId:$eventId})
    RETURN r
    """
    result=session.run(query,studentId=studentId,eventId=eventId)
    rating={}
    #Get the DIRECT and INDIRECT ratings
    for record in result:
        rating[record["r"].type]=record["r"]
    score+=0 if not('DIRECT' in rating.keys()) else float(rating['DIRECT']['rating'])/10 if 'rating' in rating['DIRECT'].keys() else 0
    score+=0 if not('INDIRECT' in rating.keys()) else float(rating['INDIRECT']['rating'])/10 if 'rating' in rating['INDIRECT'].keys() else 0
    #FIXME For now, just have INDIRECT rating equal to DIRECT rating
    #FIXME Person is interested in the club that hosted this event
    r1 = """MATCH path = (n:Event {EventId:$eventId})-[:ATTENDED]-(o:Student {StudentId:$studentId}) RETURN n.Topics as event_topics,  o.Topics  as student_topics"""
    r2 = """MATCH path = (n:Event {EventId:$eventId})-[:HOSTED_BY]-(o:Club) RETURN n.Topics as event_topics,  o.Topics  as club_topics"""
    r3 = """MATCH (n:Student {StudentId:$studentId}) RETURN n.Topics as student_topics"""
    result1 = session.run(r1,eventId=eventId,studentId=studentId)
    result2 = session.run(r2, eventId=eventId)
    result3 = session.run(r3, studentId=studentId)
    records3 = list(result3)
    student_topic = ""
    if records3:
        for record in records3:
            student_topic = ast.literal_eval(record["student_topics"])
    records2 = list(result2)
    if records2:
        for record in records2:
            club_topics = ast.literal_eval(record["club_topics"])
            if student_topic != "":
                sim = calculate_weighted_similarity(student_topic, club_topics)
            else:
                sim = 0
        score= (score+ sim)/2
    records1 = list(result1) 
    if records1:
        for record in records1:
            event_topics = ast.literal_eval(record["event_topics"])
            student_topics = ast.literal_eval(record["student_topics"])
            sim = calculate_weighted_similarity(student_topics, event_topics)
    return score/3  #Return the average rating

def studentClubSim(session,studentId,clubId,**kwargs):
    #Check if club and student IDs are valid IDs
    query=f"""
    MATCH (s:Student {{StudentId:$studentId}}),(c:Club {{ClubId:$clubId}})
    RETURN s,c
    """
    result=session.run(query,studentId=studentId,clubId=clubId)
    records=[]
    for record in result:
        records.append(record)
    if(records==[]):
        return None
    #Check if student is a member of the club
    query="""
    MATCH (s:Student {StudentId:$studentId})-[r:MEMBER_OF]-(c:Club {ClubId:$clubId})
    RETURN r
    """
    #FIXME Add campus field to student and event venue field to event. If Club from same campus more likely student affinity
    result=session.run(query,studentId=studentId,clubId=clubId).single()
    score=0 if result is None else 1
    #Find out the extent to which the student likes events hosted by the club
    query="""
    MATCH (c:Club {ClubId:$clubId})-[HOSTED_BY]-(event)-[r:DIRECT|INDIRECT]-(s:Student {StudentId:$studentId})
    RETURN AVG(toFloat(r.rating)) as avg,COUNT(r) as count
    """
    result=session.run(query,clubId=clubId,studentId=studentId).single()
    score+=0 if result["avg"] is None else result["avg"]/10
    #Find the number of events hosted by the club that the student has attended
    '''
    Use the Logistic function to restrict the count to be a value between 0 and 1
    (A/(1+e^(-x)))-1
    '''
    score+=0 if result["count"]==0 else 2/(1+math.exp(-result["count"]/2))-1
    r = """
    MATCH path = (n:Club {ClubId:$clubId})-[:MEMBER_OF]-(o:Student {StudentId:$studentId})
    RETURN n.Topics as club_topics,  o.Topics  as student_topics
    """
    result=session.run(r,clubId=clubId,studentId=studentId)
    records = list(result) 
    if records:
        for record in records:
            club_topics = ast.literal_eval(record["club_topics"])
            student_topics = ast.literal_eval(record["student_topics"])
            sim = calculate_weighted_similarity(student_topics, club_topics)
            score = (score+sim) / 2
    else:
        pass    #OPTIMIZE
    return score/3

def eventClubSim(session,eventId,clubId,**kwargs):
    query="""
    MATCH (e:Event {EventId:$eventId}),(c:Club {ClubId:$clubId})
    RETURN e,c
    """
    result=session.run(query,eventId=eventId,clubId=clubId)
    temp=result.single()
    if temp is None:
        return None
    event,club=temp["e"],temp["c"]
    #CHECK Do we need to add the factor that event is hosted by club or not?
    #Sanitize event types
    temp=event["EventType"][1:-1].split(',')
    temp=[x.strip()[1:-1] for x in temp]
    score=1 if club["ClubDomain"] in temp else 0
    #Get the avg. event rating for all events hosted by the club
    query="""
    MATCH (c:Club {ClubId:$clubId})-[HOSTED_BY]-(e:Event)
    MATCH (e)-[r:DIRECT|INDIRECT]-()
    RETURN AVG(toFloat(r.rating)) as avg
    """
    result=session.run(query,clubId=clubId).single()
    temp1=0 if result["avg"] is None else result["avg"]
    #Compare the avg. rating to event's avg. rating
    query="""
    MATCH (e:Event {EventId:$eventId})-[r:DIRECT|INDIRECT]-()
    RETURN AVG(toFloat(r.rating)) as avg
    """
    result=session.run(query,eventId=eventId).single()
    temp2=0 if result["avg"] is None else result["avg"]
    #OPTIMIZE Add a global rule for strong preference for higher event rating or do it locally like this?
    #If event is rated higher, stronger relationship between club and event
    score+=temp2/10
    temp=abs(temp1-temp2)
    #CHECK Best way to handle cases where temp1=0 or/and temp2=0
    score+= 0.5 if temp1 == 0 or temp2 == 0 else (1 if temp1 == temp2 or temp<1 else 1 / temp)
    #Get the avg. number of participants for all events hosted by the club
    query="""
    MATCH (c:Club {ClubId:$clubId})-[HOSTED_BY]-(e:Event)
    MATCH (e)-[r:DIRECT]-()
    WITH COUNT(DISTINCT e) as n,COUNT(r) as x
    RETURN x,n
    """
    result=session.run(query,clubId=clubId).single()
    temp=0 if result["n"]==0 else float(result["x"])/result["n"]
    #Get the number of participants for the event
    query="""
    MATCH (e:Event {EventId:$eventId})-[r:DIRECT]-()
    RETURN count(r) as count
    """
    result=session.run(query,clubId=clubId,eventId=eventId)
    #Compare the number of participants to the avg. number of participants obtained previously
    temp=abs(temp-result.single()["count"])
    score+=1 if temp==0 else 1/temp
    return score/3  #Noramlize score

def analyzeMetapathsNeighbourhood(session,studentId):
    #studentName=studentName.strip()
    query="""
    MATCH (s:Student {StudentId:$studentId})
    RETURN s
    """
    result=session.run(query,studentId=studentId)
    root=result.single()["s"]
    #TODO Include the 5 metapaths between any 2 students
    metapaths={'meta_SCE':'(source)-[:MEMBER_OF]-(:Club)-[:HOSTED_BY]-(:Event)',
               'meta_SCS':'(source)-[:MEMBER_OF]-(:Club)-[:MEMBER_OF]-(:Student)',
               'meta_SEC':'(source)-[:DIRECT]-(:Event)-[:HOSTED_BY]-(:Club)',
               'meta_SES':'(source)-[:DIRECT]-(:Event)-[:DIRECT]-(:Student)'}
    for key in metapaths.keys():
        paths=returnMetapaths(session,studentId,metapaths[key])
        query=f"""
            MATCH (n:Student)
            WHERE n.StudentId=$studentId
            SET n.{key}='{len(paths)}'
            RETURN n
            """
        session.run(query,studentId=root['StudentId'])

def fetchInteractions(session,studentId:str,eventId:str):
    query="""
    MATCH (s:Student {StudentId:$studentId}), (e:Event {EventId:$eventId})
    RETURN s,e
    """
    result=session.run(query,studentId=studentId,eventId=eventId).single()
    if result is None:
        return None
    query="""
    MATCH (s:Student {StudentId:$studentId})-[r:INDIRECT]-(e:Event {EventId:$eventId})
    RETURN r.liked as liked,r.remind as remind,r.bookmarked as bookmarked,r.registered as registered
    """
    result=session.run(query,studentId=studentId,eventId=eventId).single()
    if result is None:
        return {'liked':False,'remind':False,'bookmarked':False,'registered':False}
    return {'liked':False if result['liked'] is None else result['liked'],
            'remind':False if result['remind'] is None else result['remind'],
            'bookmarked':False if result['bookmarked'] is None else result['bookmarked'],
            'registered':False if result['registered'] is None else result['registered']
            }

def main():
    try:
        # Define your Neo4j connection parameters
        uri = "bolt://localhost:7687"
        #username = getSecret('secrets.json',['neo4jdb','username'])
        #password = getSecret('secrets.json',['neo4jdb','password'])
        username = getSecret(['neo4jdb','username'])
        password = getSecret(['neo4jdb','password'])

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
                #compareEvents(session,'6781','7856',True)
                compareStudents(session,'4','583',True)

    except exceptions.Neo4jError as e:
        print("Neo4j error:", e)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()