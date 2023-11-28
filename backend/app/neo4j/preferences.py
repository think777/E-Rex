from neo4j import GraphDatabase
from typing import List
from itertools import combinations
import ast  # Import the ast module for literal_eval
import json

uri = "bolt://localhost:7687"
username = 'neo4j'
password = 'testtest'

driver=GraphDatabase.driver(uri,auth=(username,password))
session=driver.session()

def clubpref(session,student_node):
    #print(student_node)
    result = session.run(
    "MATCH (s:Student {StudentId: $student_id})-[]->(c:Club) "
    "RETURN c",
    student_id=student_node["StudentId"].strip(),
    )

    clubs_attributes = [record["c"] for record in result]

    # Initialize a dictionary to store the counts of each attribute value
    attribute_value_counts = {}

    # Initialize a dictionary to store the total counts for each attribute
    attribute_total_counts = {}

    # Iterate over all clubs and count the occurrences of each value for each attribute
    for club in clubs_attributes:
        for attribute_key, attribute_value in club.items():
            # Skip 'Club' attribute, 'ClubDescription', and attributes that have None values
            if attribute_key != 'Club' and attribute_key != 'ClubDescription' and attribute_value is not None:
                # Count the occurrences of each value for the attribute
                value_counts = attribute_value_counts.get(attribute_key, {})
                value_counts[attribute_value] = value_counts.get(attribute_value, 0) + 1
                attribute_value_counts[attribute_key] = value_counts

                # Count the total occurrences for each attribute
                attribute_total_counts[attribute_key] = attribute_total_counts.get(attribute_key, 0) + 1
    
    # Initialize a dictionary to store the attribute details
    club_details = {}
    # Display the normalized counts and score for each attribute value
    print("Normalized counts and score for each attribute value:")
    for attribute_key, value_counts in attribute_value_counts.items():
        total_count = attribute_total_counts.get(attribute_key, 0)
        if total_count > 1:
            print(f"\nAttribute: {attribute_key}")
            for value, count in value_counts.items():
                # Check if there are multiple values before calculating the score
                if len(value_counts) > 1:
                    # Calculate the differences between all possible counts for a single given attribute key
                    differences = [abs(count1 - count2) for count1 in value_counts.values() for count2 in value_counts.values()]
                    
                    # Take the absolute values, add them up, and normalize between 0 and 1
                    total_difference = sum(differences)
                    score = total_difference / (total_count * (total_count - 1))
                else:
                    # Use the count as the score when there's only one value
                    score = 1

                # Normalize the count for each attribute value
                normalized_count = count / total_count

                #print(f"Value: {value}")
                #print(f"Normalized Count: {normalized_count}")
                #print(f"Score: {score}")

            # Initialize a dictionary to store details for the current attribute
            attribute_info = {
                'Score': score,
                'ValueCounts': {value: count for value, count in value_counts.items()}
            }
            
            # Add the attribute details to the main dictionary
            club_details[attribute_key] = attribute_info


    # Convert the nested data to a JSON string
    nested_data_json = json.dumps(club_details)

    session.run(
    "MATCH  (s:Student {StudentId: $student_id}) "
    "SET s.ClubDetails = $club_details",
    club_details=nested_data_json,
    student_id=student_node["StudentId"].strip(),
    )

        
def eventpref(session,student_node):
    result = session.run(
    "MATCH (s:Student {StudentId: $student_id})-[]->(e:Event) "
    "RETURN e",
    student_id=student_node["StudentId"].strip(),
    )
    clubs_attributes = [record["e"] for record in result]

    # Initialize a dictionary to store the counts of each attribute value
    attribute_value_counts = {}

    # Initialize a dictionary to store the total counts for each attribute
    attribute_total_counts = {}

    # Iterate over all clubs and count the occurrences of each value for each attribute
    for club in clubs_attributes:
        for attribute_key, attribute_value in club.items():
            # Skip 'Club' attribute, 'ClubDescription', and attributes that have None values
            if attribute_key != 'Event' and attribute_key != 'EventDescription' and attribute_value is not None:
                try:
                    # Attempt to convert the string representation of a list to an actual list
                    value_list = ast.literal_eval(attribute_value)
                    if isinstance(value_list, list):
                        # If the conversion is successful and it's a list, iterate through the values
                        for value in value_list:
                            # Count the occurrences of each value for the attribute
                            value_counts = attribute_value_counts.get(attribute_key, {})
                            value_counts[value] = value_counts.get(value, 0) + 1
                            attribute_value_counts[attribute_key] = value_counts

                            # Count the total occurrences for each attribute
                            attribute_total_counts[attribute_key] = attribute_total_counts.get(attribute_key, 0) + 1
                    else:
                        # If the conversion is not a list, process it as a single value
                        value_counts = attribute_value_counts.get(attribute_key, {})
                        value_counts[attribute_value] = value_counts.get(attribute_value, 0) + 1
                        attribute_value_counts[attribute_key] = value_counts

                        # Count the total occurrences for each attribute
                        attribute_total_counts[attribute_key] = attribute_total_counts.get(attribute_key, 0) + 1
                except (ValueError, SyntaxError):
                    # Handle the case where the conversion fails, process the value as a single value
                    value_counts = attribute_value_counts.get(attribute_key, {})
                    value_counts[attribute_value] = value_counts.get(attribute_value, 0) + 1
                    attribute_value_counts[attribute_key] = value_counts

                    # Count the total occurrences for each attribute
                    attribute_total_counts[attribute_key] = attribute_total_counts.get(attribute_key, 0) + 1

    # Initialize a dictionary to store the attribute details
    event_details = {}
    # Display the normalized counts and score for each attribute value
    print("Normalized counts and score for each attribute value:")
    for attribute_key, value_counts in attribute_value_counts.items():
        total_count = attribute_total_counts.get(attribute_key, 0)
        if total_count > 1:
            print(f"\nAttribute: {attribute_key}")
            for value, count in value_counts.items():
                # Check if there are multiple values before calculating the score
                if len(value_counts) > 1:
                    # Calculate the differences between all possible counts for a single given attribute key
                    differences = [abs(count1 - count2) for count1 in value_counts.values() for count2 in value_counts.values()]
                    
                    # Take the absolute values, add them up, and normalize between 0 and 1
                    total_difference = sum(differences)
                    score = total_difference / (total_count * (total_count - 1))
                else:
                    # Use the count as the score when there's only one value
                    score = 1

                # Normalize the count for each attribute value
                normalized_count = count / total_count

                #print(f"Value: {value}")
                #print(f"Normalized Count: {normalized_count}")
                #print(f"Score: {score}")

            # Initialize a dictionary to store details for the current attribute
            attribute_info = {
                'Score': score,
                'ValueCounts': {value: count for value, count in value_counts.items()}
            }
            
            # Add the attribute details to the main dictionary
            event_details[attribute_key] = attribute_info


    # Convert the nested data to a JSON string
    nested_data_json = json.dumps(event_details)

    session.run(
    "MATCH  (s:Student {StudentId: $student_id}) "
    "SET s.EventDetails = $event_details",
    event_details=nested_data_json,
    student_id=student_node["StudentId"].strip(),
    )









# Retrieve all Student nodes
student_nodes = session.run("MATCH (s:Student {StudentId: '1'}) RETURN s")
# Loop through each Student node and create relationships with clubs
for record in student_nodes:
        student_node = record["s"]
        clubpref(session, student_node)
        eventpref(session, student_node)







'''

def jaccard_similarity(set1: set, set2: set) -> float:
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0.0

def calculate_similarity_score(attribute_set1: set, attribute_set2: set) -> float:
    return jaccard_similarity(attribute_set1, attribute_set2)


# Initialize a dictionary to store aggregated similarity scores for each attribute
    average_similarity_scores = {}

    # Iterate over all pairs of attributes
    for attribute_key in clubs_attributes[0].keys():
        # Skip 'Club' attribute as it is not used for comparison
        if attribute_key != 'Club':
            # Initialize a list to store similarity scores for each pair of clubs
            attribute_scores = []

            # Iterate over all pairs of clubs
            for club1, club2 in combinations(clubs_attributes, 2):
                attribute_set1 = set(str(club1.get(attribute_key, '')).split())
                attribute_set2 = set(str(club2.get(attribute_key, '')).split())

                # Calculate similarity score for each attribute
                attribute_similarity = calculate_similarity_score(attribute_set1, attribute_set2)
                attribute_scores.append(attribute_similarity)

            print(attribute_scores)
            # Calculate the average similarity score for the attribute across all pairs of clubs
            average_similarity = sum(attribute_scores) / len(attribute_scores) if attribute_scores else 0.0

            # Store the aggregated similarity score for the attribute
            average_similarity_scores[attribute_key] = average_similarity

    # Update the student node with the aggregated similarity scores for each attribute
    for attribute_key, average_similarity in average_similarity_scores.items():
        # Adjust property name as needed
        print(attribute_key+":")
        print(average_similarity)
    
        #student_node[f"AverageSimilarityScore_{attribute_key}"] = average_similarity

            # Initialize dictionaries to store aggregated similarity scores and keyword compositions for each attribute
    aggregated_similarity_scores = {}
    aggregated_keyword_compositions = {}

    # Iterate over all attributes
    for attribute_key in clubs_attributes[0].keys():
        # Skip 'ClubName' attribute as it is not used for comparison
        if attribute_key != 'ClubName':
            # Initialize variables to store aggregated similarity score and keyword composition
            total_similarity = 0.0
            total_keyword_composition = set()

            # Iterate over all pairs of clubs
            for club1, club2 in combinations(clubs_attributes, 2):
                attribute_set1 = set(str(club1.get(attribute_key, '')).split())
                attribute_set2 = set(str(club2.get(attribute_key, '')).split())

                # Calculate similarity score for each attribute
                attribute_similarity = calculate_similarity_score(attribute_set1, attribute_set2)

                # Aggregate similarity score and keyword composition
                total_similarity += attribute_similarity
                total_keyword_composition.update(attribute_set1.intersection(attribute_set2))

            # Store aggregated similarity score for each attribute
            aggregated_similarity_scores[attribute_key] = total_similarity / len(list(combinations(clubs_attributes, 2)))

            # Store aggregated keyword composition for each attribute
            aggregated_keyword_compositions[attribute_key] = list(total_keyword_composition)

    # Display aggregated similarity scores and keyword compositions
    for attribute_key, similarity_score in aggregated_similarity_scores.items():
        keyword_composition = aggregated_keyword_compositions.get(attribute_key, [])
        print(f"Attribute: {attribute_key}")
        print(f"Aggregated Similarity Score: {similarity_score}")
        print(f"Keyword Composition: {keyword_composition}")
        print("------------------------")
'''