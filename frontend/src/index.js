import React from 'react';
import ReactDOM from 'react-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import App from './App';

ReactDOM.render(
  <GoogleOAuthProvider clientId="539132721173-dkriib6hvhup3f6f0ktij4l7lklj29er.apps.googleusercontent.com">
    <App />
  </GoogleOAuthProvider>,
  document.getElementById('root')
);
