// ===========================================
// Root App Component
// Defines all application routes
// ===========================================
import { Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Routes>
      <Route path="/" element={<div>Storemesh — Coming Soon</div>} />
    </Routes>
  );
}

export default App;
