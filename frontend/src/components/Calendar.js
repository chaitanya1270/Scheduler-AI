import MailComposer from 'nodemailer/lib/mail-composer';
import React, { useEffect, useState } from 'react';

const Calendar = () => {
  const [calendarData, setCalendarData] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    const fetchCalendarData = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setErrorMessage('Unauthorized, please log in');
        window.location.href = '/calendar';
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/calendar', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        setCalendarData(data);
      } catch (error) {
        setErrorMessage('Failed to fetch calendar data');
      }
    };

    fetchCalendarData();
  }, []);

  return (
    <div>
      {errorMessage ? (
        <p>{errorMessage}</p>
      ) : (
        <div>
          <h1>Your Calendar Data:</h1>
          <pre>{JSON.stringify(calendarData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default Calendar;
