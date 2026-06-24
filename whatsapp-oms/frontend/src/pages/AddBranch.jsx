import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api.js";

export default function AddBranch() {
  const nav = useNavigate();
  const [f, setF] = useState({
    tenant_id: "", name: "", branch_location: "", whatsapp_number: "",
    logo_url: "", currency: "PKR", opening_hours: "", delivery_radius_km: 5,
  });
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setMsg(null);
    try {
      const { data } = await api.post("/admin/tenants", {
        tenant_id: f.tenant_id,
        name: f.name,
        branch_location: f.branch_location,
        whatsapp_number: f.whatsapp_number,
        logo_url: f.logo_url || null,
        config: {
          currency: f.currency,
          opening_hours: f.opening_hours,
          delivery_radius_km: Number(f.delivery_radius_km),
        },
      });
      setMsg(data);
    } catch (e2) {
      setErr(e2.response?.data?.detail || "Failed to create branch");
    }
  };

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-bold mb-4">Add New Branch</h1>
      {err && <p className="text-red-600 mb-2">{err}</p>}
      {msg && (
        <div className="bg-green-50 border border-green-200 rounded p-4 mb-4 text-sm">
          <p className="font-semibold text-green-700">Branch provisioned! 🎉</p>
          <p className="break-all">Webhook URL: <code>{msg.webhook_url}</code></p>
          <p>Migrations applied: {msg.migrations_applied.join(", ") || "(already current)"}</p>
          <button onClick={() => nav("/dashboard/branches")}
            className="mt-2 underline text-green-700">Go to Branches →</button>
        </div>
      )}
      <form onSubmit={submit} className="space-y-3 bg-white p-6 rounded-xl shadow">
        <Field label="Tenant ID (lowercase_underscore)" v={f.tenant_id} on={set("tenant_id")} req />
        <Field label="Restaurant Name" v={f.name} on={set("name")} req />
        <Field label="Branch Location" v={f.branch_location} on={set("branch_location")} req />
        <Field label="WhatsApp Number (+...)" v={f.whatsapp_number} on={set("whatsapp_number")} req />
        <Field label="Logo URL" v={f.logo_url} on={set("logo_url")} />
        <div className="grid grid-cols-3 gap-2">
          <Field label="Currency" v={f.currency} on={set("currency")} />
          <Field label="Opening Hours" v={f.opening_hours} on={set("opening_hours")} />
          <Field label="Delivery Radius (km)" v={f.delivery_radius_km} on={set("delivery_radius_km")} />
        </div>
        <button className="bg-black text-white rounded px-4 py-2 w-full hover:bg-gray-800">
          Provision Branch
        </button>
      </form>
    </div>
  );
}

function Field({ label, v, on, req }) {
  return (
    <label className="block text-sm">
      <span className="text-gray-600">{label}</span>
      <input className="mt-1 w-full border rounded px-3 py-2" value={v}
        onChange={on} required={req} />
    </label>
  );
}
