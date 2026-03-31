import React from 'react';
import { useNavigate } from 'react-router-dom';

const GoogleSignUp = () => {
  const navigate = useNavigate();

  const handleGoogleLogin = () => {
    // Redirect to the FastAPI backend to initiate Google OAuth
    window.location.href = "http://localhost:8000/google";
  };

  return (
    <main className="card-container slideUp-animation">
      <div className="image-container">
        <h1 className="company">Meeting Assist<sup>&trade;</sup></h1>
        <img src="./assets/images/signUp.svg" className="illustration" alt="Sign up" />
        <p className="quote">Sign up for better meeting management..!</p>
      </div>

      <div className="form-container slideRight-animation">
        <h1 className="form-header">Get started</h1>

        {/* Google Sign-Up Button */}
        <button type="button" className="submit-btn" onClick={handleGoogleLogin}>
          <i className="fa-brands fa-google fa-flip" style={{ color: '#f90606' }}></i>
          Continue with Google
        </button>

        {/* Optional: Outlook Sign-Up Button (Placeholder) */}
        <button className="submit-btn">
          <i className="fa-thin fa-envelope-open-text fa-flip" style={{ color: "#74C0FC" }}></i> 
          Continue with Outlook
        </button>
      </div>
    </main>
  );
};

export default GoogleSignUp;
