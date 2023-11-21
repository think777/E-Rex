from neo4j import GraphDatabase
from .helper import studentClubSim, studentEventSim

uri = "bolt://localhost:7687"
username = 'neo4j'
password = 'testtest'

driver=GraphDatabase.driver(uri,auth=(username,password))
session=driver.session()

