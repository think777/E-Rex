import pandas as pd
from collections import defaultdict
from neo4j import GraphDatabase,exceptions
import csv
import random
#from backend.app.neo4j.helper import create_relationships_with_clubs,create_relationships_with_events

uri = "bolt://localhost:7687"
username = 'neo4j'
password = 'testtest'

driver=GraphDatabase.driver(uri,auth=(username,password))
session=driver.session()

# Load data from CSV files
students_df = pd.read_csv('Events List - Students.csv')
clubs_df = pd.read_csv('Events List - Clubs(2).csv')
events_df = pd.read_csv('Events List - before_20_02_2024.csv')

# Split the list of clubs in the Clubs column and add specific club keywords to the student's keywords
students_df['Clubs'] = students_df['Clubs'].str.replace('[', '').str.replace(']', '').str.replace("'", '').str.replace('"','')
students_df['Clubs'] = students_df['Clubs'].str.split(',')

# Assuming Keywords column in students and clubs contain a list of interests separated by commas
students_df['Keywords'] = students_df['Keywords'].str.replace('[', '').str.replace(']', '').str.replace("'", '').str.replace('"','').str.split(',')
clubs_df['Keywords'] = clubs_df['Keywords'].str.replace('[', '').str.replace(']', '').str.replace("'", '').str.replace('"','').str.split(',')
events_df['Keywords'] = events_df['Keywords'].str.replace('[', '').str.replace(']', '').str.replace("'", '').str.replace('"','').str.split(',')

#print(students_df['Keywords'])

dist_dict = defaultdict(int)

# Iterate through each student
for index, student_row in students_df.iterrows():
    student_id = student_row['StudentID']
    student_name = student_row['Name']
    student_interests = student_row['Keywords']
    student_clubs = student_row['Clubs']

    # Iterate through each club the student is part of
    for club in student_clubs:
        
        # Find the club in the clubs DataFrame
        club_info = clubs_df[clubs_df['Club'] == club.strip()]
       
        # If the club is found, add its keywords to the student's interests
        if not club_info.empty:
            club_keywords = club_info['Keywords'].iloc[0]
            student_interests.extend(club_keywords)

        else:
            print (student_name)
            print (club)

    # Find events with a match score above the specified threshold
    matching_events = []
    matching_events_ratings = []
    for event_index, event_row in events_df.iterrows():
        event_keywords = event_row['Keywords']

        # Calculate the match score (number of common keywords)
        match_score = len(set(student_interests) & set(event_keywords))

        # Check if match percentage is above the threshold
        if match_score >= 2:
            matching_events.append(event_row['EventID'])
            session.run(
                "MATCH (s:Student {StudentID: $student_id})"
                "MATCH (e:Event {EventID: $event_id})"
                "MERGE (s)-[:ATTENDED]->(e)",
                student_id=student_id,
                event_id=event_row['EventID']
            )
            dist_dict[match_score] += 1
            # Assign ratings based on match score
            ratings = min(10, max(1, match_score + random.uniform(-1, 5)))
            matching_events_ratings.append(ratings)
            session.run(
                "MATCH (s:Student {StudentID: $student_id})-[r:ATTENDED]->(e:Event {EventID: $event_id})"
                "SET r.rating = $rating",
                student_id=student_id,
                event_id=event_row['EventID'],
                rating=ratings
            )
            print(f"Node created between {student_id} and {event_row['EventID']}")

    #print(best_match_score)
    #print(matching_events)
    # Update the 'Events Attended' column with the matching event IDs
    student_row['Events Attended'] = matching_events
    
print(dist_dict)
#print(best_match_score)
print(students_df) 