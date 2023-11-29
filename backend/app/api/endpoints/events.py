from . import *
from typing import List, Dict
from enum import Enum
from app.neo4j.helper import compareStudents, compareEvents, studentEventSim, studentClubSim, fetchInteractions, addNodeHandler, modifyNodeHandler, removeNodeHandler

router=APIRouter(prefix='/event',tags=["Event"])

session=db.getSession()

class Interaction(BaseModel):
    studentId: str
    eventId: str
    interaction: str
    status: bool

class Event(BaseModel):
    EventDate: str
    EventDuration: str
    EventType: List[str]
    PrizePool: str
    Event: str
    EventID: str
    EventRating: str
    ClubId: str
    EventDescription: str


class EventProfile(BaseModel):
    pass

class ClubProfile(BaseModel):
    pass

class StudentProfile(BaseModel):
    pass

class Preferences(BaseModel):
    pass

#FIXME Do not send the preferences to user. Send only the required properties(check other props. as well)

class Student(BaseModel):
    ClubName: List[str]
    EmailId: str
    meta_SCS: str
    Semester: str
    CGPA: str
    meta_SES: str
    SRN: str
    Name: str
    StudentID: str
    LinkedIn: str
    meta_SCE: str
    Branch: str
    EventID: List[int]
    PhoneNumber: str
    meta_SEC: str

class Club(BaseModel):
    Campus: str
    Club: str
    ClubDescription: str
    ClubDomain: str
    ClubHasWebsite: int
    ClubID: int
    ClubSocials: str

class NodeType(str,Enum):
    Student="Student"
    Club="Club"
    Event="Event"

class AddRequest(BaseModel):
    node: Event|Club|Student
    nodeType: NodeType

class ModifyRequest(BaseModel):
    node: Event|Club|Student
    nodeId: str

class RemoveRequest(BaseModel):
    nodeId:str
    nodeType: NodeType

@router.get('/interaction/get')
async def getInteractions(sid:str=Query(description="Student ID"),eid:str=Query(descirption="Event ID")):
    result=fetchInteractions(session,sid,eid)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid IDs")
    return result

@router.post('/interaction/set')
async def setInteractions(request: Interaction):
    if request.interaction in ['liked','bookmarked','remind','registered']:
        result=spidey.assessChanges(request.interaction,request.status,request.studentId,request.eventId)
        if(result is None):
            # Handle the exception and return a 404 response
            raise HTTPException(status_code=404, detail="Invalid IDs!")
        nType,=result.labels
        return spidey.weave(nType,result[nType+'ID'],False)
    else:
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid action!")

@router.post('/addNode')
async def addNode(request: AddRequest):
    result=addNodeHandler(session,request.nodeType,request.node.model_dump())
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Unable to add node")
    return result

@router.post('/modifyNode')
async def modifyNode(request:ModifyRequest):
    result=modifyNodeHandler(session,request.node.model_dump(),request.nodeId)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Unable to modify node")
    return result

@router.post('/removeNode')
async def removeNode(request:RemoveRequest):
    result=removeNodeHandler(session,request.nodeType,request.nodeId)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Unable to remove node")
    return result