import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import CallDetails from './pages/CallDetails';
import Appointments from './pages/Appointments';
import Settings from './pages/Settings';
import Layout from './components/Layout';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/calls/:callId" element={<CallDetails />} />
        <Route path="/appointments" element={<Appointments />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  );
}

export default App;

