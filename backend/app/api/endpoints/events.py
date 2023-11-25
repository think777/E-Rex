from . import *
from app.neo4j.helper import compareStudents, compareEvents, studentEventSim, studentClubSim, fetchInteractions

router=APIRouter(prefix='/event',tags=["Event"])

session=db.getSession()

class Interaction(BaseModel):
    studentId: str
    eventId: str
    interaction: str
    status: bool

@router.get('/interaction/get')
async def getInteractions(sid:str=Query(description="Student ID"),eid:str=Query(descirption="Event ID")):
    result=fetchInteractions(session,sid,eid)
    if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid IDs")
    return result

@router.post('/interaction/set')
async def handleInteractions(request: Interaction):
    if request.interaction in ['liked','bookmarked','remind','registered']:
        print(request)
        result=spidey.assessChanges(request.interaction,request.status,request.studentId,request.eventId)
        if(result is None):
            # Handle the exception and return a 404 response
            raise HTTPException(status_code=404, detail="Invalid IDs!")
        nType,=result.labels
        return spidey.weave(nType,result[nType+'Id'])
    else:
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid action!")

@router.post('/register')
async def registerEvent(studentId:str=Query(description="ID of student"),eventId:str=Query(description="ID of event")):
    '''if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid student ID")'''
    return None

@router.post('/like')
async def likeEvent(studentId:str=Query(description="ID of student"),eventId:str=Query(description="ID of event")):
    '''if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid student ID")'''
    return None

@router.post('/rate')
async def rateEvent(studentId:str=Query(description="ID of student"),eventId:str=Query(description="ID of event")):
    '''if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid student ID")'''
    return None

@router.post('/bookmark')
async def bookmarkEvent(studentId:str=Query(description="ID of student"),eventId:str=Query(description="ID of event")):
    '''if(result is None):
        # Handle the exception and return a 404 response
        raise HTTPException(status_code=404, detail="Invalid student ID")'''
    return None