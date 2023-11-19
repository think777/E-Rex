#The main graph traversal algorithm

from neo4j import GraphDatabase
from .helper import studentClubSim, studentEventSim
from app.utils.secretHandler import getSecret

uri = "bolt://localhost:7687"
username = getSecret(['testdb','username'])
password = getSecret(['testdb','password'])

driver=GraphDatabase.driver(uri,auth=(username,password))
session=driver.session()

def insertSorted(iterable:list, elem:tuple):
    #Helper #OPTIMIZE
    #PROTOTYPE
    '''
    iterable: sorted list of tuples
    tuple: (nodeId,similarity_score)
    sorting: based on similarity_score
    elem: tuple mentioned above
    '''
    #Use binary search to find index to insert elem in iterable
    start=0
    length=len(iterable)
    end=length
    mid=int(end/2)
    while(start<=end and start<length):
        if(elem[1]==iterable[mid][1]):
            break
        elif(elem[1]>iterable[mid][1]):
            start=mid+1
        else:
            end=mid-1
        mid=int((start+end)/2)
    iterable.insert(start,elem)

metapaths={
    "student":{
        "club":{
            "event":{
                "student":1
            },
            "student":2
        },
        "event":{
            "student":3,
            "club":{
                "event":{
                    "student":4
                },
                "student":5
            }
        }
    }
}

class Spider():
    def __init__(self):
        self.queue=[]
        self.rel_weights={
            "SS":1,
            "SE":1,
            "SC":1
            }
    
    def construct(self):
        pass
    
    def weave(self,studentId:str):
        nodeQueue={"Student":[],"Club":[],"Event":[]}
        query="MATCH (s:Student {StudentId: $studentId}) RETURN s"
        result=session.run(query,studentId=studentId)
        currNode=result.single()["s"]
        '''
        In order to avoid revisiting paths, we need to be aware of visited relationships.
        Hence, mark edges visited.
        '''
        query="MATCH ()-[r]-() WHERE type(r) <> 'SILK_ROAD' SET r.visited=0 "
        session.run(query)
        query="MATCH (s:Student {StudentId: $studentId})-[r]-(neighbour) WHERE type(r) <> 'SILK_ROAD' SET r.visited=1 RETURN DISTINCT(neighbour) as neighbour"
        result=session.run(query,studentId=studentId)
        temp=[]        
        #whether neighbours exist or not, take the entire graph, predict edge weights

        for record in result:
            temp.append(record)
            label,=record["neighbour"].labels
            nodeQueue[label].append(record["neighbour"]) 
        if(len(temp) == 0):
            print("No neighbours!")
            return 0
        for club in nodeQueue["Club"]:
            score=studentClubSim(session,currNode["StudentId"],club["ClubId"],True)
            #Weight the score
            score*=self.rel_weights["SC"]
            #Store the sim. score
            query="""
            MATCH (s:Student {StudentId: $studentId}), (c:Club {ClubId: $clubId})
            MERGE (s)-[r:SILK_ROAD]-(c)
            SET r.weight=$score
            """
            session.run(query,studentId=currNode["StudentId"],clubId=club["ClubId"],score=score)
        for event in nodeQueue["Event"]:
            score=studentEventSim(session,currNode["StudentId"],event["EventId"],True)
            #Weight the score
            score*=self.rel_weights["SE"]
            #Store the sim. score
            query="""
            MATCH (s:Student {StudentId: $studentId}), (e:Event {EventId: $eventId})
            MERGE (s)-[r:SILK_ROAD]-(e)
            SET r.weight=$score
            """
            session.run(query,studentId=currNode["StudentId"],eventId=event["EventId"],score=score)
            '''
            Next steps:
            1) Make weave recursive wrt student nodes. Complete all other SILK_ROAD gens.(like event, club) in current weave only.
            '''
        return "hello"
    
    def crawl(self,studentId:str):
        #TODO Need to account for supply of session either as an arg or as an attribute of the Spider()
        query="""
        MATCH (s:Student {StudentId:$studentId})
        RETURN s
        """
        result=session.run(query,studentId=studentId)
        print(result)
        print("hello")
        temp=result.single()
        if temp is None:
            return None
        studNode=temp['s']
        self.queue=[]
        query="""
        MATCH (e:Event)
        WHERE date(datetime({ epochmillis: apoc.date.parse(e.EventDate, 'ms', 'dd-MM-yyyy') })) > date()
        RETURN e;
        """
        query="""
        MATCH (e:Event)
        WHERE date(datetime({ epochmillis: apoc.date.parse(e.EventDate, 'ms', 'dd-MM-yyyy') })) > date($currDate)
        RETURN e;
        """
        currDate="2023-01-01"
        result=session.run(query,currDate=currDate)
        eventList=[]
        for record in result:
            eventList.append(record["e"])
        return eventList

    def assessChanges(self):
        pass