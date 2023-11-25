#The main graph traversal algorithm

from neo4j import GraphDatabase
from .helper import studentClubSim, studentEventSim, eventClubSim, analyzeMetapathsNeighbourhood
from .preferences import clubpref,eventpref
from app.utils.secretHandler import getSecret
import math
import json
from datetime import *

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
            frozenset({'S','S'}):1,
            frozenset({'E','E'}):1,
            frozenset({'S','E'}):1,
            frozenset({'S','C'}):1,
            frozenset({'E','C'}):1
        }
    
    def construct(self):
        #When the graph is constructed initially, all the nodes need to be marked as unvisited
        query="""
        MATCH (s)
        SET s.visited=0
        """
        session.run(query)
    
    def weave(self,nType:str,nodeId:str):
        nodeQueue=[]

        def weaveNeighbourhood(node):
            nodeType,=node.labels
            neighbourQueue={"Student":[],"Club":[],"Event":[]}
            query=f"""
            MATCH (node:{nodeType} {{{nodeType+'Id'}: $nodeId}})-[r]-(neighbour)
            WHERE type(r) <> 'SILK_ROAD'
            RETURN DISTINCT neighbour as neighbour
            """
            result=session.run(query,nodeId=node[nodeType+"Id"])

            for record in result:
                if record["neighbour"]["visited"]==0:
                    nodeQueue.append(record["neighbour"])
                label,=record["neighbour"].labels
                neighbourQueue[label].append(record["neighbour"])
            
            for labelType in neighbourQueue.keys():
                for neighbour in neighbourQueue[labelType]:
                    nodeTypes=frozenset({nodeType[0],labelType[0]})
                    simFuncHandler=self.helper('simFuncHandler')
                    simFunc=simFuncHandler(nodeTypes)
                    arg1 = neighbour["StudentId"] if 'Student' in neighbour.labels else node["StudentId"] if 'Student' in node.labels else None
                    arg2 = neighbour["EventId"] if 'Event' in neighbour.labels else node["EventId"] if 'Event' in node.labels else None
                    arg3 = neighbour["ClubId"] if 'Club' in neighbour.labels else node["ClubId"] if 'Club' in node.labels else None
                    score=simFunc(session,studentId=arg1,eventId=arg2,clubId=arg3)
                    #Weigh the score
                    score*=self.rel_weights[nodeTypes]
                    #Store the sim. score as SILK_ROAD attribute
                    query=f"""
                    MATCH (node1:{nodeType} {{{nodeType+'Id'}: $id1}}), (node2:{labelType} {{{labelType+'Id'}: $id2}})
                    MERGE (node1)-[r:SILK_ROAD]-(node2)
                    SET r.weight=$score
                    """
                    session.run(query,id1=node[nodeType+'Id'],id2=neighbour[labelType+'Id'],score=score)
            
            #Mark the node as visited
            query=f"""
            MATCH (node:{nodeType} {{{nodeType+'Id'}: $nodeId}})
            SET node.visited=1
            """
            session.run(query,nodeId=node[nodeType+"Id"])

        #Get the node in question
        query=f"""
        MATCH (node:{nType} {{{nType+'Id'}: $nodeId}})
        RETURN node
        """
        result=session.run(query,nodeId=nodeId).single()
        if result is None:
            return None
        nodeQueue.append(result["node"])

        while True:
            try:
                #Get the checkVisited function
                checkVisited=self.helper('checkVisited')
                #Check if node has already been visited
                if checkVisited(nodeQueue[0]):
                    nodeQueue.pop(0)
                else:
                    temp,=nodeQueue[0].labels
                    if temp=='Student':
                        analyzeMetapathsNeighbourhood(session,nodeQueue[0]["StudentId"])
                        clubpref(session,nodeQueue[0])
                        eventpref(session,nodeQueue[0])
                    weaveNeighbourhood(nodeQueue.pop(0))
            except IndexError:
                break

        return True
    
    def crawl(self,studentId:str):
        #TODO Need to account for supply of session either as an arg or as an attribute of the Spider()
        '''
        PROTOTYPE
        nodeQueue=[
        (dist,node),....
        ]
        dist: distance of node from start node
        '''
        nodeQueue=[]
        '''
        PROTOTYPE
        eventDict={
            eventId:{
                scores:[dist,..],
                visited: n,
                event: node
            },
            ...
        }
        '''
        eventDict={}
        currDate=date(2023,1,1)
        distDict={'Student':{},'Event':{},'Club':{}}
        query="""
        MATCH (s:Student {StudentId:$studentId})
        RETURN s
        """
        result=session.run(query,studentId=studentId)
        temp=result.single()
        if temp is None:
            return None
        startNode=temp['s']
        eventpref(session,startNode)
        #In order to avoid revisiting paths, we need to be aware of visited relationships. Hence, mark edges visited.
        query="""
        MATCH ()-[r]-()
        WHERE type(r) <> 'SILK_ROAD'
        SET r.visited=0
        """
        session.run(query)
        nodeQueue.append((0,startNode))
        while True:
            if nodeQueue.isEmpty:
                break
            currDist,currNode=nodeQueue.pop(0)
            nodeType,=currNode.labels
            #Get neighbours
            query=f"""
            MATCH (node:{nodeType} {{{nodeType+'Id'}:$nodeId}})-[r]-(neighbour)
            WHERE type(r)<>'SILK_ROAD'
            WITH node,neighbour
            MATCH node-[r:SILK_ROAD]-neighbour
            RETURN r.weight as weight,neighbour
            """
            result=session.run(query,nodeId=currNode[nodeType+'Id'])
            for record in result:
                #Calculate score for node
                score=currDist+1/record["weight"]
                #Keep track of the nodes encountered(will act as parents in the next iteration) and their scores
                nodeQueue.append((score,record["neighbour"]))
                #Get the type of the node
                temp,=record["neighbour"].labels
                #Check if the node is an event
                if temp=="Event":
                    #Convert the event's date to python datetime object
                    temp1=record["neighbour"]["EventDate"].split('-')
                    eventDate=date(int(temp1[2]),int(temp1[1]),int(temp1[0]))
                    #Check if event is an upcoming event
                    if eventDate>currDate:
                        #Check if event has already been visited
                        if record["neighbour"]["EventId"] in eventDict:
                            eventDict[record["neighbour"]["EventId"]]["scores"].append(score)
                            eventDict[record["neighbour"]["EventId"]]["visited"]+=1
                        else:
                            eventDict[record["neighbour"]["EventId"]]={"scores":[score],"visited":1,"event":record["neighbour"]}
            

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
        result=session.run(query,currDate=currDate)
        eventDict={}
        for record in result:
            temp=record["e"]._properties
            temp["score"]=0
            eventDict[record["e"]["EventId"]]=temp
        query="""
        MATCH p=(startNode:Student {StudentId: $studentId})-[:SILK_ROAD*]->(endNode:Event {EventId: $eventId})
        WITH p, REDUCE(dist = 0.0, rel in relationships(p) | dist+(1/rel.weight)) AS distance
        RETURN p, distance
        ORDER BY distance ASC
        """
        for eventId in eventDict.keys():
            result=session.run(query,studentId=currNode["StudentId"],eventId=eventId)
            pathDist=[]
            calcPreferenceMatch=self.helper('calcPreferenceMatch')
            preferenceScore=calcPreferenceMatch(currNode['EventDetails'],eventId)
            for record in result:
                if not(math.isinf(record['distance'])):
                    pathDist.append(record["distance"])
            if len(pathDist)==0:
                eventDict[eventId]["score"]=preferenceScore
            else:
                eventDict[eventId]["score"]=round(sum(pathDist)/len(pathDist)*math.exp(len(pathDist))/math.pow(2,len(pathDist)),2)+preferenceScore
        sortedList=sorted(eventDict.values(), key=lambda x: x["score"], reverse=True)
        return sortedList

    def assessChanges(self,action:str,val:bool,studentId:str,eventId:str):
        '''
        TODO
            3) Create a function to handle preferences
            5) Fix analyze neighbourhood
            9) Add the fact that higher the event rating, greater the preference(ground rule)
            10) Do a path analysis for similarity functions
            11) Send scores seperately
            12) Mark nodes affected
            13) Differentiate interactions(event addition, student addition, club addition, removal, etc.) and interactions
            14) Cleanup code and push
        '''
        query="""
        MATCH (s:Student {StudentId:$studentId}), (e:Event {EventId:$eventId})
        RETURN s,e
        """
        result=session.run(query,studentId=studentId,eventId=eventId).single()
        if result is None:
            return None
        student,event=result["s"],result["e"]
        #Make the required changes in the graph
        query=f"""
        MATCH (s:Student {{StudentId:$studentId}}),(e:Event {{EventId:$eventId}})
        MERGE (s)-[r:INDIRECT]-(e)
        SET r.{action}=$val
        RETURN r
        """
        result=session.run(query,studentId=studentId,eventId=eventId,val=val).single()
        interactionsHandler=self.helper('indirectInteractionsHandler')
        score=interactionsHandler(result["r"]._properties)
        query="""
        MATCH (s:Student {StudentId:$studentId}),(e:Event {EventId:$eventId})
        MERGE (s)-[r:INDIRECT]-(e)
        SET r.rating=$score
        RETURN r
        """
        result=session.run(query,studentId=studentId,eventId=eventId,score=score).single()
        #Mark affected nodes
        query="""
        MATCH (e:Event {EventId:$eventId})-[]->(neighbor)
        SET e.visited = 0, neighbor.visited = 0
        """
        session.run(query,eventId=eventId)
        query="""
        MATCH (s:Student {StudentId:$studentId})-[]->(neighbor)
        SET s.visited = 0, neighbor.visited = 0
        RETURN s
        """
        result=session.run(query,studentId=studentId).single()
        return result["s"]

    def helper(self,funcName):
        def checkVisited(node):
            label,=node.labels
            query=f"""
            MATCH (x:{label} {{{label+'Id'}:$nodeId}})
            RETURN x.visited as visited
            """
            result=session.run(query,nodeId=node[label+"Id"]).single()
            return result["visited"]==1
        
        def simFuncHandler(types:frozenset):
            simFuncDict={
                frozenset({'S','C'}): studentClubSim,
                frozenset({'S','E'}): studentEventSim,
                frozenset({'E','C'}): eventClubSim
            }
            return simFuncDict[types]
        
        def indirectInteractionsHandler(rel):
            weights={'liked':10,'bookmarked':10,'remind':10,'registered':10}
            score=0
            for key in rel:
                score+=0 if not(rel[key]) else weights[key] if key in weights else 0
            return score/4
        
        def calcPreferenceMatch(eventProfile,eventId):
            query="""
            MATCH (node:Event {EventId:$eventId})
            RETURN node
            """
            result=session.run(query,eventId=eventId).single()
            event=result["node"]
            score=0
            eventProfile=json.loads(eventProfile)
            for attr in eventProfile:
                if event[attr] in eventProfile[attr]["ValueCounts"]:
                    score+= eventProfile[attr]["Score"]*eventProfile[attr]["ValueCounts"][event[attr]]
                else:
                    pass
            return score

        #Create a dictionary with keys as function names and their values as the corresponding functions
        nested_functions = {name: value for name, value in locals().items() if callable(value)}
        return nested_functions[funcName]