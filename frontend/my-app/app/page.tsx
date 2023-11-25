'use client'

// pages/index.tsx
import React, { useState, useEffect } from 'react';
import Swal from 'sweetalert2';

import Logo from './components/Logo';
import Row from './components/Row';

const Home: React.FC = () => {

  type EventType = {
    EventDate: string;
    EventDuration: string;
    EventType: string[];
    PrizePool: string;
    Event: string;
    EventId: string;
    EventRating: string;
    ClubId: string;
    EventDescription: string;
    score: number;
  };

  const [query, setQuery] = useState<string>('');
  const [result, setResult] = useState<EventType[]|null>(null);
  const [isPopoverVisible, setPopoverVisible] = useState(false);
  const [isLoading, setLoading] = useState<boolean>(false);
  const [eventStatus, setEventStatus] = useState<{ [key: string]: { liked: boolean; remind: boolean; bookmarked: boolean; registered: boolean } }>(() => {
    if (!result) {
      // Handle the case when result is null
      return {};
    }
  
    return result.reduce((acc, event) => {
      acc[event.EventId] = { liked: false, bookmarked: false, remind: false, registered: false }; // Initialize status for each event
      return acc;
    }, {});
  });

  const handleRegistration = (event: EventType) => {
    // Perform registration logic here for the specific event (use 'eventId')
    // For demonstration purposes, we'll just toggle the registration status
  setLoading(true);
  // Notify the API
  const apiUrl = 'http://127.0.0.1:8000/event/interaction/set'; // Replace with your actual API endpoint
  const requestBody = {
    studentId: query,
    eventId: event.EventId,
    interaction: 'registered',
    status: !eventStatus[event.EventId]?.registered,
  };

  fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // You may need to include additional headers (e.g., authentication token)
    },
    body: JSON.stringify(requestBody),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error('Failed to notify API');
      }
      return response.json();
    })
    .then((data) => {
      // Handle API response if needed
      if(eventStatus[event.EventId]?.registered)
      {
        Swal.fire({
          icon: 'info',
          title: 'Registered!',
          text: `You have already registered for the event "${event.Event}".`,
          html: `You have already registered for the event "<strong>${event.Event}</strong>".`,
          });
      }
      else
      {
        // Display a custom styled alert
        Swal.fire({
          icon: 'success',
          title: 'Registration successful!',
          text: `You have successfully registered for the event "${event.Event}"!`,
          html: `You have successfully registered for the event "<strong>${event.Event}</strong>"!`,
        });
        setEventStatus((prev) => ({
          ...prev,
          [event.EventId]: {
            ...prev[event.EventId],
            ['registered']: !prev[event.EventId]?.registered,
          },
        }));
      }
      fetchData();
    })
    .catch((error) => {
      console.error('Error notifying API:', error);
      // Handle error if needed
      if(eventStatus[event.EventId]?.registered)
      {
        Swal.fire({
          icon: 'error',
          title: 'Unable to remove registration!',
          text: `Unable to take back your registration for the event "${event.Event}".`,
          html: `Unable to take back your registration for the event "<strong>${event.Event}</strong>".`,
          });
      }
      else
      {
        // Display a custom styled alert
        Swal.fire({
          icon: 'success',
          title: 'Registration unsuccessful...',
          text: `We couldn't register you for the event "${event.Event}"...`,
          html: `We couldn't register you for the event "<strong>${event.Event}</strong>"...`,
        });
      }
    });
  };

  const handleLike = (event: EventType) => {
  setLoading(true);
  // Notify the API
  const apiUrl = 'http://127.0.0.1:8000/event/interaction/set';
  const requestBody = {
    studentId: query,
    eventId: event.EventId,
    interaction: 'liked',
    status: !eventStatus[event.EventId]?.liked,
  };
  fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // You may need to include additional headers (e.g., authentication token)
    },
    body: JSON.stringify(requestBody),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error('Failed to notify API');
      }
      return response.json();
    })
    .then((data) => {
      // Handle API response if needed
      // Display alert
      !eventStatus[event.EventId]?.liked
      ?Swal.fire({
        icon: 'success',
        title: 'Liked!',
        text: `You have liked the event ${event.Event}!`,
        html: `You have liked the event "<strong>${event.Event}</strong>"!`,
      })
      :Swal.fire({
        icon: 'error',
        title: 'Unliked!',
        text: `Like for event ${event.Event} has been removed...`,
        html: `Like for event "<strong>${event.Event}</strong>" has been removed...`,
      });
      // Your logic for handling 'like' button click
      setEventStatus((prev) => ({
        ...prev,
        [event.EventId]: {
          ...prev[event.EventId],
          ['liked']: !prev[event.EventId]?.liked,
        },
      }));
      fetchData();
    })
    .catch((error) => {
      console.error('Error notifying API:', error);
      // Handle error if needed
      // Display alert
      !eventStatus[event.EventId]?.liked
      ?Swal.fire({
        icon: 'error',
        title: 'Unable to like...',
        text: `Your like couldn't be registered for the event ${event.Event}...`,
        html: `Your like couldn't be registered for the event "<strong>${event.Event}</strong>"...`,
      })
      :Swal.fire({
        icon: 'error',
        title: 'Unable to unlike...',
        text: `Like for event ${event.Event} couldn't be removed...`,
        html: `Like for event "<strong>${event.Event}</strong>" couldn't  be removed...`,
      });
    });
  };

  const handleReminder = (event: EventType) => {
  setLoading(true);
  // Notify the API
  const apiUrl = 'http://127.0.0.1:8000/event/interaction/set';
  const requestBody = {
    studentId: query,
    eventId: event.EventId,
    interaction: 'remind',
    status: !eventStatus[event.EventId]?.remind,
  };

  fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // You may need to include additional headers (e.g., authentication token)
    },
    body: JSON.stringify(requestBody),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error('Failed to notify API');
      }
      return response.json();
    })
    .then((data) => {
      // Handle API response if needed
      // Display alert
      !eventStatus[event.EventId]?.remind
      ?Swal.fire({
        icon: 'success',
        title: 'Reminder set!',
        text: `We will remind you about the event ${event.Event} on ${event.EventDate}.`,
        html: `We will remind you about the event "<strong>${event.Event}</strong>" on <strong>${event.EventDate}</strong>.`,
      })
      :Swal.fire({
        icon: 'warning',
        title: 'Reminder removed!',
        text: `Reminder for event ${event.Event} has been removed....`,
        html: `Reminder for event "<strong>${event.Event}</strong>" has been removed....`,
      });
      // Your logic for handling 'like' button click
      setEventStatus((prev) => ({
        ...prev,
        [event.EventId]: {
          ...prev[event.EventId],
          ['remind']: !prev[event.EventId]?.remind,
        },
      }));
      fetchData();
    })
    .catch((error) => {
      console.error('Error notifying API:', error);
      // Handle error if needed
      // Display alert
      !eventStatus[event.EventId]?.remind
      ?Swal.fire({
        icon: 'error',
        title: 'Reminder not set!',
        text: `We weren't able to set the reminder for the event ${event.Event}.`,
        html: `We weren't able to set the reminder for the event "<strong>${event.Event}</strong>".`,
      })
      :Swal.fire({
        icon: 'error',
        title: "Reminder couldn't be removed!",
        text: `Reminder for event ${event.Event} coudn't be removed....`,
        html: `Reminder for event "<strong>${event.Event}</strong>" couldn't be removed....`,
      });
    });
  };

  const handleBookmark = (event: EventType) => {
  setLoading(true);
  // Notify the API
  const apiUrl = 'http://127.0.0.1:8000/event/interaction/set';
  const requestBody = {
    studentId: query,
    eventId: event.EventId,
    interaction: 'bookmarked',
    status: !eventStatus[event.EventId]?.bookmarked,
  };

  fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // You may need to include additional headers (e.g., authentication token)
    },
    body: JSON.stringify(requestBody),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error('Failed to notify API');
      }
      return response.json();
    })
    .then((data) => {
      // Handle API response if needed
      // Display alert
      !eventStatus[event.EventId]?.bookmarked
      ?Swal.fire({
        icon: 'info',
        title: 'Bookmarked!',
        text: `Event ${event.Event} has been bookmarked.`,
        html: `Event "<strong>${event.Event}</strong>" has been bookmarked.`,
      })
      :Swal.fire({
        icon: 'warning',
        title: 'Oh no..',
        text: `Bookmark for event ${event.Event} has been removed...`,
        html: `Bookmark for event "<strong>${event.Event}</strong>" has been removed...`,
      });
      // Your logic for handling 'bookmark' button click
      setEventStatus((prev) => ({
        ...prev,
        [event.EventId]: {
          ...prev[event.EventId],
          ['bookmarked']: !prev[event.EventId]?.bookmarked,
        },
      }));
      fetchData();
    })
    .catch((error) => {
      console.error('Error notifying bookmark API:', error);
      // Handle error if needed
      !eventStatus[event.EventId]?.bookmarked
      ?Swal.fire({
        icon: 'error',
        title: 'Unable to bookmark...',
        text: `Event ${event.Event} couldn't be bookmarked.`,
        html: `Event "<strong>${event.Event}</strong>" coudn't be bookmarked.`,
      })
      :Swal.fire({
        icon: 'error',
        title: 'Oh no..',
        text: `Bookmark for event ${event.Event} coundn't be removed...`,
        html: `Bookmark for event "<strong>${event.Event}</strong>" coudn't be removed...`,
      });
    });
  };

  const fetchData = async () => {
    try {
      // Your data fetching logic here
      const response = await fetch(`http://127.0.0.1:8000/spider/crawl?id=${query}`);
      const data = await response.json();
      setResult(data);

      let temp = {};
      //FIXME Make this one GET request instead of multiple
      for (let record in data) {
        const result = await fetch(
          `http://127.0.0.1:8000/event/interaction/get?sid=${query}&eid=${data[record].EventId}`
        );
        const dict = await result.json();
        temp[data[record].EventId] = dict;
      }
      setEventStatus(temp);
    } catch (error) {
      console.error('Error fetching data:', error);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true); // Set loading state to true
    fetchData();
    // Hide the popover after form submission
    setPopoverVisible(false);
  };
  return (
    <div className="container mx-auto p-4">
      <h1>Enter the student's ID</h1>
      {/* Display the list of InfoRows */}
      {/*<div>
        {infoData.map((data, index) => (
          <Row key={index} data={data} />
        ))}
        </div>
      */}
      <form onSubmit={handleFormSubmit} className="mb-4">
          <label htmlFor="search" className="mb-2 text-sm font-medium text-gray-900 sr-only dark:text-white">
            Search
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
            <svg
                className="w-4 h-4 text-gray-500 dark:text-gray-400"
                aria-hidden="true"
                xmlns="http://www.w3.org/2000/svg"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M10 0a10 10 0 1 0 10 10A10.011 10.011 0 0 0 10 0Zm0 5a3 3 0 1 1 0 6 3 3 0 0 1 0-6Zm0 13a8.949 8.949 0 0 1-4.951-1.488A3.987 3.987 0 0 1 9 13h2a3.987 3.987 0 0 1 3.951 3.512A8.949 8.949 0 0 1 10 18Z"/>
              </svg>
            </div>
            <input
              type="search"
              id="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="block w-full p-4 ps-10 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
              placeholder="Student ID"
              required
            />
            <button
              type="submit"
              className="text-white absolute end-2.5 bottom-2.5 bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-4 py-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
              onMouseEnter={() => setPopoverVisible(true)}
              onMouseLeave={() => setPopoverVisible(false)}
            >
              Recommend Events
            </button>
            {isPopoverVisible && (
              <div
              data-popover
              role="tooltip"
              className="absolute z-10 visible inline-block w-64 text-sm text-gray-500 transition-opacity duration-300 bg-white border border-gray-200 rounded-lg shadow-sm opacity-100 dark:text-gray-400 dark:border-gray-600 dark:bg-gray-800"
              style={{ top: '-170%', right: '0' }}
              >
                <div className="px-3 py-2 bg-gray-100 border-b border-gray-200 rounded-t-lg dark:border-gray-600 dark:bg-gray-700">
                  <h3 className="font-semibold text-gray-900 dark:text-white">Recommend?</h3>
                </div>
                <div className="px-3 py-2">
                  <p>Don't worry</p>
                  <p>Spider will do the work for you!</p>
                </div>
                <div data-popper-arrow></div>
              </div>
            )}
          </div>
        </form>
        {/* Loading Section */}
        {isLoading && 
        <div className="fixed inset-0 flex items-center justify-center bg-gray-800 dark:bg-gray-900 opacity-50">
          <svg
            aria-hidden="true"
            className="w-16 h-16 text-gray-200 animate-spin dark:text-gray-600 fill-blue-600"
            viewBox="0 0 100 101"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
              fill="currentColor"
            />
            <path
              d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
              fill="currentColor"
            />
          </svg>
          <span className="text-white-200 dark:text-white-600 ml-4 text-lg">Loading...</span>
        </div>
        }
         {result !== null && !isLoading &&(
          Object.keys(result).length != 1?(
            <ol className="relative my-8 border-s border-gray-200 dark:border-gray-700">
            {result.map((event, index) => (
              <li key={index} className="mb-10 ms-6 opacity-70 hover:opacity-100">
                <span className="absolute my-4 flex items-center justify-center w-6 h-6 bg-blue-100 rounded-full -start-3 ring-8 ring-white dark:ring-gray-900 dark:bg-blue-900">
                  <svg className="w-2.5 h-2.5 text-blue-800 dark:text-blue-300" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M20 4a2 2 0 0 0-2-2h-2V1a1 1 0 0 0-2 0v1h-3V1a1 1 0 0 0-2 0v1H6V1a1 1 0 0 0-2 0v1H2a2 2 0 0 0-2 2v2h20V4ZM0 18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8H0v10Zm5-8h10a1 1 0 0 1 0 2H5a1 1 0 0 1 0-2Z"/>
                  </svg>
              </span>
              <div className="group justify-center items-center relative cursor-pointer overflow-hidden transition-transform duration-500 transform hover:scale-105 hover:translate-y-[-8px] hover:translate-x-8">
                <div className="p-4 hover:border transform hover:bg-gray-800 hover:border-white-800 hover:rounded-lg">
                <div className="flex items-center space-x-4">
              <div className="flex-grow">
                {/* ... (Existing code) */}
                <h3 className="flex items-center mb-1 text-lg font-semibold text-gray-900 dark:text-white">
                  {event.Event}{' '}
                  <span className="bg-blue-100 text-blue-800 text-sm font-medium me-2 px-2.5 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300 ms-3">Latest</span>
                </h3>
                <time className="block mb-2 text-sm font-normal leading-none text-gray-400 dark:text-gray-500">
                  Released on {event.EventDate}
                </time>
              </div>
                <div className="flex items-center space-x-2 ml-auto">
                  {/* Like Button */}
                  <button
                    className="flex items-center space-x-2 px-3 py-1"
                    onClick={() => handleLike(event)}
                  >
                    {eventStatus[event.EventId]?.liked
                    ?<svg className="h-6 w-6 text-red-500 opacity-75 hover:scale-125 hover:opacity-100"  fill="red" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                    </svg>
                    :<svg className="h-6 w-6 text-red-500 opacity-75 hover:scale-125 hover:opacity-100"  fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                    </svg>
                    }
                  </button>
                  
                  {/* Reminder Button */}
                  <button
                    className="flex items-center space-x-2 px-3 py-1"
                    onClick={() => handleReminder(event)}
                  >
                    {eventStatus[event.EventId]?.remind
                    ?<svg className="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="white" viewBox="0 0 20 20">
                      <path d="M15.133 10.632v-1.8a5.406 5.406 0 0 0-4.154-5.262.955.955 0 0 0 .021-.106V1.1a1 1 0 0 0-2 0v2.364a.946.946 0 0 0 .021.106 5.406 5.406 0 0 0-4.154 5.262v1.8C4.867 13.018 3 13.614 3 14.807 3 15.4 3 16 3.538 16h12.924C17 16 17 15.4 17 14.807c0-1.193-1.867-1.789-1.867-4.175ZM4 4a1 1 0 0 1-.707-.293l-1-1a1 1 0 0 1 1.414-1.414l1 1A1 1 0 0 1 4 4ZM2 8H1a1 1 0 0 1 0-2h1a1 1 0 1 1 0 2Zm14-4a1 1 0 0 1-.707-1.707l1-1a1 1 0 1 1 1.414 1.414l-1 1A1 1 0 0 1 16 4Zm3 4h-1a1 1 0 1 1 0-2h1a1 1 0 1 1 0 2ZM6.823 17a3.453 3.453 0 0 0 6.354 0H6.823Z"></path>
                    </svg>
                    :<svg className="w-5 h-5 text-white opacity-75 hover:scale-125 hover:opacity-100" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 21">
                      <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 3.464V1.1m0 2.365a5.338 5.338 0 0 1 5.133 5.368v1.8c0 2.386 1.867 2.982 1.867 4.175C17 15.4 17 16 16.462 16H3.538C3 16 3 15.4 3 14.807c0-1.193 1.867-1.789 1.867-4.175v-1.8A5.338 5.338 0 0 1 10 3.464ZM1.866 8.832a8.458 8.458 0 0 1 2.252-5.714m14.016 5.714a8.458 8.458 0 0 0-2.252-5.714M6.54 16a3.48 3.48 0 0 0 6.92 0H6.54Z"></path>
                  </svg>
                  }
                  </button>
                  
                  {/* Bookmark Button */}
                  <button
                    className="flex items-center space-x-2 px-3 py-1"
                    onClick={() => handleBookmark(event)}
                  >
                    {eventStatus[event.EventId]?.bookmarked
                    ?<svg className="w-6 h-6 text-yellow-500 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="yellow" viewBox="0 0 14 20">
                    <path d="M13 20a1 1 0 0 1-.64-.231L7 15.3l-5.36 4.469A1 1 0 0 1 0 19V2a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v17a1 1 0 0 1-1 1Z"></path>
                </svg>
                    :<svg className="w-5 h-5 text-yellow-500 opacity-75 hover:scale-125 hover:opacity-100" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 20">
                      <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m13 19-6-5-6 5V2a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17Z"></path>
                  </svg>}
                  </button>
                </div>
                </div>
                <p className="mb-4 text-base font-normal text-gray-500 dark:text-gray-400">{event.EventDescription}</p>
        
                {/* Showcase other event attributes in the timeline */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="mb-4 text-sm font-normal leading-none text-gray-400 dark:text-gray-500">
                    Event Duration: {event.EventDuration} minutes
                  </div>
                  <div className="mb-4 text-sm font-normal leading-none text-gray-400 dark:text-gray-500">
                    Prize Pool: ${event.PrizePool}
                  </div>
                  <div className="mb-4 text-sm font-normal leading-none text-gray-400 dark:text-gray-500">
                    Event Type: {Array.isArray(event.EventType) ? event.EventType.join(', ') : event.EventType}
                  </div>
                  <div className="mb-4 text-sm font-normal leading-none text-gray-400 dark:text-gray-500">
                    Event Rating: {event.EventRating}
                  </div>
                  <div className="mb-4 text-sm font-normal leading-none text-gray-400 dark:text-gray-500">
                    Club ID: {event.ClubId}
                  </div>
                  <div className="mb-4 text-sm font-normal leading-none text-gray-400 dark:text-gray-500">
                    Event ID: {event.EventId}
                  </div>
                </div>
                {/* Display score at the bottom right */}
                <div className="absolute right-8 mb-2 mr-2 text-lg font-semibold text-gray-900 dark:text-white">
                  Score: {event.score}
                </div>
                <a
                  href="#"
                  onClick={() => handleRegistration(event)}
                  className={`inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg ${
                    eventStatus[event.EventId]?.registered
                      ? 'bg-green-500 text-white border border-green-800 hover:bg-green-600 focus:ring-green-300'
                      : 'text-gray-900 bg-white border border-gray-200 hover:bg-gray-100 focus:z-10 focus:ring-4 focus:outline-none focus:ring-gray-200'
                  } dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600 dark:hover:text-white dark:hover:bg-gray-700 dark:focus:ring-gray-700`}
                >
                  {eventStatus[event.EventId]?.registered ? (
                    <>
                      <svg className="w-6 h-6 text-green-500 dark:text-green" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 21 21">
                        <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m6.072 10.072 2 2 6-4m3.586 4.314.9-.9a2 2 0 0 0 0-2.828l-.9-.9a2 2 0 0 1-.586-1.414V5.072a2 2 0 0 0-2-2H13.8a2 2 0 0 1-1.414-.586l-.9-.9a2 2 0 0 0-2.828 0l-.9.9a2 2 0 0 1-1.414.586H5.072a2 2 0 0 0-2 2v1.272a2 2 0 0 1-.586 1.414l-.9.9a2 2 0 0 0 0 2.828l.9.9a2 2 0 0 1 .586 1.414v1.272a2 2 0 0 0 2 2h1.272a2 2 0 0 1 1.414.586l.9.9a2 2 0 0 0 2.828 0l.9-.9a2 2 0 0 1 1.414-.586h1.272a2 2 0 0 0 2-2V13.8a2 2 0 0 1 .586-1.414Z"></path>
                      </svg>
                      Registered!
                    </>
                  ) : (
                    'Register Now'
                  )}
                </a>
                </div>
                {/* shine box */}
                <div className="absolute top-0 -inset-full h-full w-1/2 z-5 block transform -skew-x-12 bg-gradient-to-r from-transparent to-white opacity-20 group-hover:animate-shine" />
                </div>
              </li>
            ))}
          </ol>
        )
        :(<div className="flex p-4 mb-4 text-sm text-red-800 border border-red-300 rounded-lg bg-red-50 dark:bg-gray-800 dark:text-red-400" role="alert">
        <svg className="flex-shrink-0 inline w-4 h-4 me-3 mt-[2px]" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z"/>
        </svg>
        <span className="sr-only">Danger</span>
        <div>
          <span className="font-medium">Invalid input! Potential fixes:</span>
            <ul className="mt-1.5 list-disc list-inside">
              <li>Ensure that you give the <strong><i>correct ID</i></strong> of the student</li>
              <li>Ensure that the <strong><i>student exists</i></strong></li>
              <li>Ensure that you <strong>follow the format</strong> of the ID(in this case, <strong><i>integer input required</i></strong>)</li>
          </ul>
        </div>
      </div>))}
    </div>
  );
};

export default Home;