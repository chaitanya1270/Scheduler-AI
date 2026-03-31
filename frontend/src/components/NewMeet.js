import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const NewMeet = () => {
  const [emails, setEmails] = useState(['']);
  const navigate = useNavigate();

  const handleEmailChange = (index, event) => {
    const updatedEmails = [...emails];
    updatedEmails[index] = event.target.value;
    setEmails(updatedEmails);
  };

  const handleAddEmail = () => {
    setEmails([...emails, '']);
  };

  const handleNext = () => {
    const validEmails = emails.filter(email => /\S+@\S+\.\S+/.test(email));
    if (validEmails.length === emails.length) {
      navigate('/time-slot');
    } else {
      alert('Please enter valid emails.');
    }
  };

  return (
    <div className="new-meet">
      <h2>New Meeting</h2>
      {emails.map((email, index) => (
        <input
          key={index}
          type="email"
          value={email}
          onChange={(event) => handleEmailChange(index, event)}
          placeholder="Enter email"
        />
      ))}
      <button onClick={handleAddEmail}>Add Another Email</button>
      <button onClick={handleNext}>Next</button>
    </div>
  );
};

export default NewMeet;
