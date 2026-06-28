import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { WorkspaceProvider } from './contexts/WorkspaceContext';
import { LandingPage } from './pages/LandingPage';
import { WorkspacePage } from './pages/WorkspacePage';

function App() {
  return (
    // Default to dark theme on body
    <div className="dark">
      <WorkspaceProvider>
        <Router>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/workspace/:owner/:repo" element={<WorkspacePage />} />
          </Routes>
        </Router>
      </WorkspaceProvider>
    </div>
  );
}

export default App;
