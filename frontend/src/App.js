import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import GoogleSignUp from './components/GoogleSignUp';
import CalendarPage from './components/Calendar';
import NewMeet from './components/NewMeet';
import './App.css';

function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          <Route path="/" element={<GoogleSignUp />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/new-meet" element={<NewMeet />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
