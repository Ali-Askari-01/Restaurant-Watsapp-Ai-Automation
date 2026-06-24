import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import Sidebar from "../components/Sidebar.jsx";
import OrderTable from "../components/OrderTable.jsx";
import OrderModal from "../components/OrderModal.jsx";
import BranchCard from "../components/BranchCard.jsx";
import MenuManager from "../components/MenuManager.jsx";
import AddBranch from "./AddBranch.jsx";
import api from "../api/api.js";

function AllOrders() {
  const [orders, setOrders] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [selected, setSelected] = useState(null);
  const [filters, setFilters] = useState({ tenant_id: "", status: "", date_from: "", date_to: "" });

  const loadTenants = async () => {
    const { data } = await api.get("/admin/tenants");
    setTenants(data);
  };
  const loadOrders = async () => {
    const params = {};
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
    const { data } = await api.get("/central/orders", { params });
    setOrders(data);
  };
  useEffect(() => { loadTenants(); }, []);
  useEffect(() => { loadOrders(); }, [filters]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">All Orders</h1>
      <div className="flex flex-wrap gap-2">
        <select className="border rounded px-3 py-2"
          value={filters.tenant_id}
          onChange={(e) => setFilters({ ...filters, tenant_id: e.target.value })}>
          <option value="">All branches</option>
          {tenants.map((t) => (
            <option key={t.tenant_id} value={t.tenant_id}>
              {t.name} — {t.branch_location}
            </option>
          ))}
        </select>
        <select className="border rounded px-3 py-2" value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">All statuses</option>
          {["pending","confirmed","preparing","delivered","cancelled"].map((s) =>
            <option key={s} value={s}>{s}</option>)}
        </select>
        <input type="date" className="border rounded px-3 py-2"
          onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} />
        <input type="date" className="border rounded px-3 py-2"
          onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} />
      </div>
      <OrderTable orders={orders} onRowClick={setSelected} />
      {selected && (
        <OrderModal order={selected} onClose={() => setSelected(null)}
          onUpdated={loadOrders} />
      )}
    </div>
  );
}

function Branches() {
  const [stats, setStats] = useState([]);
  useEffect(() => {
    api.get("/central/tenants/stats").then((r) => setStats(r.data));
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Branches Overview</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((s) => <BranchCard key={s.tenant_id} s={s} />)}
      </div>
    </div>
  );
}

function Settings() {
  const [tenants, setTenants] = useState([]);
  const [sel, setSel] = useState("");
  useEffect(() => { api.get("/admin/tenants").then((r) => setTenants(r.data)); }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Settings — Menu Manager</h1>
      <select className="border rounded px-3 py-2" value={sel}
        onChange={(e) => setSel(e.target.value)}>
        <option value="">Select a branch…</option>
        {tenants.map((t) => (
          <option key={t.tenant_id} value={t.tenant_id}>
            {t.name} — {t.branch_location}
          </option>
        ))}
      </select>
      {sel && <MenuManager tenantId={sel} />}
    </div>
  );
}

export default function Dashboard() {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-6 bg-gray-100 min-h-screen">
        <Routes>
          <Route index element={<AllOrders />} />
          <Route path="branches" element={<Branches />} />
          <Route path="add-branch" element={<AddBranch />} />
          <Route path="settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
