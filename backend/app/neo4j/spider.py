#The main graph traversal algorithm

from neo4j import GraphDatabase

driver=GraphDatabase.driver(uri,auth=(username,password))
session=driver.session()

#Helper #OPTIMIZE
#PROTOTYPE
'''
iterable: sorted list of tuples
tuple: (nodeId,similarity_score)
sorting: based on similarity_score
elem: tuple mentioned above
'''
def insertSorted(iterable:list, elem:tuple):
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
    
    def construct():
        pass
    
    def weave():
        pass
    
    def crawl():
        pass

    def assessChanges():
        pass