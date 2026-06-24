import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import AddBranch from "./pages/AddBranch.jsx";
import BranchHome from "./pages/BranchHome.jsx";
import BranchMenu from "./pages/BranchMenu.jsx";
import OrderTracker from "./pages/OrderTracker.jsx";

function RequireAuth({ children }) {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      {/* Branch public website */}
      <Route path="/branch/:tenantId" element={<BranchHome />} />
      <Route path="/branch/:tenantId/menu" element={<BranchMenu />} />
      <Route path="/branch/:tenantId/track" element={<OrderTracker />} />

      {/* Owner dashboard */}
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard/*" element={<RequireAuth><Dashboard /></RequireAuth>} />
      <Route path="/dashboard/add-branch" element={<RequireAuth><AddBranch /></RequireAuth>} />

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
