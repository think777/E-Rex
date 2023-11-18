from . import *
from app.neo4j.spider import Spider
from app.neo4j.helper import compareStudents, compareEvents, studentEventSim, studentClubSim

router=APIRouter(prefix='/event',tags=["Event"])

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