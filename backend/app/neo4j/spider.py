#The main graph traversal algorithm

from neo4j import GraphDatabase
from .helper import studentClubSim, studentEventSim, eventClubSim
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
        #Weights given to different relationships
        self.rel_weights={
            frozenset({'S','S'}):1,
            frozenset({'E','E'}):1,
            frozenset({'S','E'}):1,
            frozenset({'S','C'}):1,
            frozenset({'E','C'}):1
            }
    
    def construct(self,session):
        #When the graph is constructed initially, all the nodes need to be marked as unvisited
        query="""
        MATCH (s)
        WHERE type(r) <> 'SILK_ROAD'
        SET s.visited=0
        """
        session.run(query)
    
    def weave(self,studentId:str):
        nodeQueue=[]
        def weaveNeighbourhood(node):
            nodeType,=node.labels
            neighbourQueue={"Student":[],"Club":[],"Event":[]}
            query=f"""
            MATCH (s:{type} {{{type+'Id'}: $id}})-[r]-(neighbour)
            WHERE type(r) <> 'SILK_ROAD'
            SET r.visited=1
            RETURN DISTINCT(neighbour) as neighbour
            """
            result=session.run(query,id=node[type+"Id"])
            for record in result:
                nodeQueue.append(record)
                label,=record["neighbour"].labels
                neighbourQueue[label].append(record["neighbour"])

            for club in nodeQueue["Club"]:
                nodeTypes=frozenset({nodeType[0],'C'})
                clubSimFunc=self.helper(nodeTypes)
                score=clubSimFunc(session,node["StudentId"],club["ClubId"],True)
                #Weight the score
                score*=self.rel_weights[nodeTypes]
                #Store the sim. score
                query="""
                MATCH (s:Student {StudentId: $studentId}), (c:Club {ClubId: $clubId})
                MERGE (s)-[r:SILK_ROAD]-(c)
                SET r.weight=$score
                """
                session.run(query,studentId=node["StudentId"],clubId=club["ClubId"],score=score)
            for event in nodeQueue["Event"]:
                nodeTypes=frozenset({nodeType[0],'E'})
                eventSimFunc=self.helper(nodeType,'Event')
                score=eventSimFunc(session,node["StudentId"],event["EventId"],True)
                #Weight the score
                score*=self.rel_weights[nodeTypes]
                #Store the sim. score
                query="""
                MATCH (s:Student {StudentId: $studentId}), (e:Event {EventId: $eventId})
                MERGE (s)-[r:SILK_ROAD]-(e)
                SET r.weight=$score
                """
                session.run(query,studentId=node["StudentId"],eventId=event["EventId"],score=score)
            for student in nodeQueue["Student"]:
                nodeTypes=frozenset({nodeType[0],'S'})
                studentSimFunc=self.helper(nodeTypes)
                score=studentSimFunc(session,node["StudentId"],event["EventId"],True)
                #Weight the score
                score*=self.rel_weights[nodeTypes]
                #Store the sim. score
                query="""
                MATCH (s:Student {StudentId: $studentId}), (e:Event {EventId: $eventId})
                MERGE (s)-[r:SILK_ROAD]-(e)
                SET r.weight=$score
                """
                session.run(query,studentId=node["StudentId"],eventId=event["EventId"],score=score)
            
        #Get the node in question
        query="""
        MATCH (s:Student {StudentId: $studentId})
        RETURN s
        """
        result=session.run(query,studentId=studentId).single()
        if result is None:
            return None
        nodeQueue.append(result["s"])
        while True:
            try:
                #Get the checkVisited function
                checkVisited=self.helper('checkVisited')
                #Check if node has already been visited
                if checkVisited(nodeQueue[0]):
                    nodeQueue.pop(0)
                weaveNeighbourhood(nodeQueue.pop(0))
            except IndexError:
                break
    
    def crawl(self,studentId:str):
        #TODO Need to account for supply of session either as an arg or as an attribute of the Spider()
        query="""
        MATCH (s:Student {StudentId:$studentId})
        RETURN s
        """
        result=session.run(query,studentId=studentId)
        temp=result.single()
        if temp is None:
            return None
        studNode=temp['s']
        '''
        In order to avoid revisiting paths, we need to be aware of visited relationships.
        Hence, mark edges visited.
        '''
        query="""
        MATCH ()-[r]-()
        WHERE type(r) <> 'SILK_ROAD'
        SET r.visited=0
        """
        session.run(query)
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

    def helper(self,funcName):
        def checkVisited(node):
            label,=node.labels
            query=f"""
            MATCH (x:{label} {{{label+'Id'}:$id}})
            RETURN x.visited as visited
            """
            result=session.run(query,id=node[label+"Id"]).single()
            return result["visited"]==1
        def simFuncHandler(types:frozenset):
            simFuncDict={
                frozenset({'S','C'}): studentClubSim,
                frozenset({'S','E'}): studentEventSim,
                frozenset({'E','C'}): eventClubSim
            }
            return simFuncDict[types]
        #Create a dictionary with keys as function names and their values as the corresponding functions
        nested_functions = {name: value for name, value in locals().items() if callable(value)}
        return nested_functions[funcName]