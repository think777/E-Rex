#The main graph traversal algorithm
from .helper import studentClubSim, studentEventSim, eventClubSim, analyzeMetapathsNeighbourhood
from .gen_edge_w import edgeWeightGen, find_edge_weight
#from .preferences import clubpref,eventpref
from app.utils.secretHandler import getSecret
from . import DB
import math
import json
from datetime import *

#FIXME
session=DB.getSession()

def insertSorted(iterable:list, elem:tuple):
    #Helper #OPTIMIZE
    #PROTOTYPE
    '''
    iterable: sorted list of tuples
    tuple: (nodeId,node,similarity_score)
    sorting: based on similarity_score
    elem: tuple mentioned above
    '''
    #Use binary search to find index to insert elem in iterable
    start=0
    length=len(iterable)
    end=length
    mid=int(end/2)
    while(start<=end and start<length):
        if(elem[2]==iterable[mid][2]):
            break
        elif(elem[2]>iterable[mid][2]):
            start=mid+1
        else:
            end=mid-1
        mid=int((start+end)/2)
    iterable.insert(start,elem)
    return start

def element_exists(my_list, target_element):
    counter=-1
    for tup in my_list:
        counter+=1
        if target_element in tup:
            return counter
    return -1

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
    
    def weave(self,nType:str,nodeId:str,restart:bool):
        
        if restart:
            query="""
            MATCH (s)
            SET s.visited=0
            """
            session.run(query)
        
        nodeQueue=[]

        def weaveNeighbourhood(node):
            nodeType,=node.labels
            neighbourQueue={"Student":[],"Club":[],"Event":[]}
            query=f"""
            MATCH (node:{nodeType} {{{nodeType+'ID'}: $nodeId}})-[r]-(neighbour)
            WHERE type(r) <> 'SILK_ROAD'
            RETURN DISTINCT neighbour as neighbour
            """
            result=session.run(query,nodeId=node[nodeType+"ID"])

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
                    arg1 = neighbour["StudentID"] if 'Student' in neighbour.labels else node["StudentID"] if 'Student' in node.labels else None
                    arg2 = neighbour["EventID"] if 'Event' in neighbour.labels else node["EventID"] if 'Event' in node.labels else None
                    arg3 = neighbour["ClubID"] if 'Club' in neighbour.labels else node["ClubID"] if 'Club' in node.labels else None
                    score=simFunc(session,studentId=arg1,eventId=arg2,clubId=arg3)
                    #Weigh the score
                    score*=self.rel_weights[nodeTypes]
                    #Store the sim. score as SILK_ROAD attribute
                    query=f"""
                    MATCH (node1:{nodeType} {{{nodeType+'ID'}: $id1}}), (node2:{labelType} {{{labelType+'ID'}: $id2}})
                    MERGE (node1)-[r:SILK_ROAD]-(node2)
                    SET r.weight=$score
                    """
                    session.run(query,id1=node[nodeType+'ID'],id2=neighbour[labelType+'ID'],score=score)
            
            #Mark the node as visited
            query=f"""
            MATCH (node:{nodeType} {{{nodeType+'ID'}: $nodeId}})
            SET node.visited=1
            """
            session.run(query,nodeId=node[nodeType+"ID"])

        #Get the node in question
        query=f"""
        MATCH (node:{nType} {{{nType+'ID'}: $nodeId}})
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
                        analyzeMetapathsNeighbourhood(session,nodeQueue[0]["StudentID"])
                        #clubpref(session,nodeQueue[0])
                        #eventpref(session,nodeQueue[0])
                    #Generate edge weights for node neighbourhood
                    #edgeWeightGen(session,nodeQueue[0])
                    #Create silk roads with appropriate weights
                    weaveNeighbourhood(nodeQueue.pop(0))
            except IndexError:
                break

        return True
    
    def crawl(self,studentId:str):
        #TODO Need to account for supply of session either as an arg or as an attribute of the Spider()
        '''
        PROTOTYPE
        nodeQueue=[
            (nodeId,node,dist),....
        ]
        dist: distance of node from start node
        '''
        nodeQueue=[]

        '''
        PROTOTYPE
        nodeDict={
            nodeId:(node,index),
            ...
        }
        nodeDict={}
        '''

        '''
        PROTOTYPE
        eventQueue=[(eventId,event,score),...]
        '''
        eventQueue=[]
        
        '''
        PROTOTYPE
        eventDict={
            eventId:(event,index),
            ...
        }
        eventDict={}
        '''

        currDate=datetime(2024, 2, 21, 0, 0, 0)
        query="""
        MATCH (s:Student {StudentID:$studentId})
        RETURN s
        """
        result=session.run(query,studentId=studentId)
        temp=result.single()
        if temp is None:
            return None
        startNode=temp['s']
        #eventpref(session,startNode)
        #In order to avoid revisiting paths, we need to be aware of visited relationships. Hence, mark edges visited.
        query="""
        MATCH ()-[r:SILK_ROAD]-()
        SET r.visited=0
        """
        session.run(query)
        nodeQueue.append((studentId,startNode,0))
        while True:
            #Check if nodeQueue is mepty to stop crawl()
            if not(nodeQueue):
                break
            currNodeId,currNode,currDist=nodeQueue.pop(0)
            nodeType,=currNode.labels
            #Get neighbours
            query=f"""
            MATCH (node:{nodeType} {{{nodeType+'ID'}:$nodeId}})-[r:SILK_ROAD]-(neighbour)
            WHERE r.visited=0 and r.weight<>0
            WITH r,neighbour
            SET r.visited=1
            RETURN r.weight as weight,neighbour
            """
            result=session.run(query,nodeId=currNode[nodeType+'ID'])
            for record in result:
                #Calculate score for node
                score=currDist+1/record["weight"]
                neighbour=record["neighbour"]
                neighbourType,=neighbour.labels
                #Add preference funcs. here
                
                #edge_weight=find_edge_weight(session,currNode[nodeType+"ID"],neighbour[neighbourType+'ID'])
                #score*=edge_weight if edge_weight else 1
                #Keep track of the nodes encountered(will act as parents in the next iteration) and their scores
                index=element_exists(nodeQueue,currNodeId)
                if index!=-1:
                    if score<nodeQueue[index][2]:
                        nodeQueue.pop(index)
                        insertSorted(nodeQueue,(neighbour[neighbourType+'ID'],neighbour,score))
                else:
                    insertSorted(nodeQueue,(neighbour[neighbourType+'ID'],neighbour,score))
                #Check if the node is an event
                if neighbourType=="Event":
                    #calcPreferenceMatch=self.helper('calcPreferenceMatch')
                    #preferenceScore=calcPreferenceMatch(startNode['EventDetails'],neighbour["EventID"])
                    #score+=1/preferenceScore if preferenceScore>0 else abs(preferenceScore)
                    #Convert the event's date to python datetime object
                    eventDate=datetime.strptime(neighbour["Event Date"], '%Y-%m-%d %H:%M:%S')
                    #Check if event is an upcoming event
                    if eventDate>currDate:
                        #Check if event has already been visited
                        index=element_exists(eventQueue,neighbour["EventID"])
                        if index!=-1:
                            if score<eventQueue[index][2]:
                                eventQueue.pop(index)
                                insertSorted(eventQueue,(neighbour["EventID"],neighbour,score))
                        else:
                            insertSorted(eventQueue,(neighbour["EventID"],neighbour,score))
        '''query="""
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
            eventDict[record["e"]["EventID"]]=temp
        query="""
        MATCH p=(startNode:Student {StudentID: $studentId})-[:SILK_ROAD*]->(endNode:Event {EventID: $eventId})
        WITH p, REDUCE(dist = 0.0, rel in relationships(p) | dist+(1/rel.weight)) AS distance
        RETURN p, distance
        ORDER BY distance ASC
        """
        for eventId in eventDict.keys():
            result=session.run(query,studentId=currNode["StudentID"],eventId=eventId)
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
        return sortedList'''
        result=[{'score':x[2],**x[1]._properties} for x in eventQueue]
        return result

    def assessChanges(self,action:str,val:bool,studentId:str,eventId:str):
        '''
        TODO
            3) Create a function to handle preferences
            5) Fix analyze neighbourhood
            9) Add the fact that higher the event rating, greater the preference(ground rule)
            10) Do a path analysis for similarity functions
            11) Send scores seperately
            12) Mark nodes affected
        '''
        query="""
        MATCH (s:Student {StudentID:$studentId}), (e:Event {EventID:$eventId})
        RETURN s,e
        """
        result=session.run(query,studentId=studentId,eventId=eventId).single()
        if result is None:
            return None
        student,event=result["s"],result["e"]
        #Make the required changes in the graph
        query=f"""
        MATCH (s:Student {{StudentID:$studentId}}),(e:Event {{EventID:$eventId}})
        MERGE (s)-[r:INDIRECT]-(e)
        SET r.{action}=$val
        RETURN r
        """
        result=session.run(query,studentId=studentId,eventId=eventId,val=val).single()
        interactionsHandler=self.helper('indirectInteractionsHandler')
        score=interactionsHandler(result["r"]._properties)
        query="""
        MATCH (s:Student {StudentID:$studentId}),(e:Event {EventID:$eventId})
        MERGE (s)-[r:INDIRECT]-(e)
        SET r.rating=$score
        RETURN r
        """
        result=session.run(query,studentId=studentId,eventId=eventId,score=score).single()
        #Mark affected nodes
        query="""
        MATCH (e:Event {EventID:$eventId})-[]->(neighbor)
        SET e.visited = 0, neighbor.visited = 0
        """
        session.run(query,eventId=eventId)
        query="""
        MATCH (s:Student {StudentID:$studentId})-[]->(neighbor)
        SET s.visited = 0, neighbor.visited = 0
        RETURN s
        """
        result=session.run(query,studentId=studentId).single()
        return result["s"]

    def helper(self,funcName):
        def checkVisited(node):
            label,=node.labels
            query=f"""
            MATCH (x:{label} {{{label+'ID'}:$nodeId}})
            RETURN x.visited as visited
            """
            result=session.run(query,nodeId=node[label+"ID"]).single()
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
            MATCH (node:Event {EventID:$eventId})
            RETURN node
            """
            result=session.run(query,eventId=eventId).single()
            event=result["node"]
            score=0
            n_attrs=0
            eventProfile=json.loads(eventProfile)
            for attr in eventProfile:
                n_attrs+=1
                if event[attr] in eventProfile[attr]["ValueCounts"]:
                    score+= eventProfile[attr]["Score"]*eventProfile[attr]["ValueCounts"][event[attr]]
                else:
                    pass
            return score if score else -n_attrs

        #Create a dictionary with keys as function names and their values as the corresponding functions
        nested_functions = {name: value for name, value in locals().items() if callable(value)}
        return nested_functions[funcName]