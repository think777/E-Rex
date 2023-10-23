from .db import Database

#Create a global(within neo4j/) DB driver instance
DB=Database()   #Can be used by importing app/neo4j(like a package variable)