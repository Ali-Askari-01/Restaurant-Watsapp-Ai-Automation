import { useEffect, useState } from "react";
import api from "../api/api.js";

export default function MenuManager({ tenantId }) {
  const [menu, setMenu] = useState([]);
  const [form, setForm] = useState({ name: "", price: "", category: "", description: "" });

  const load = async () => {
    const { data } = await api.get(`/tenant/${tenantId}/menu`);
    setMenu(data);
  };
  useEffect(() => { if (tenantId) load(); }, [tenantId]);

  const add = async (e) => {
    e.preventDefault();
    await api.post(`/tenant/${tenantId}/menu`, {
      ...form, price: parseFloat(form.price),
    });
    setForm({ name: "", price: "", category: "", description: "" });
    load();
  };
  const remove = async (id) => {
    await api.delete(`/tenant/${tenantId}/menu/${id}`);
    load();
  };

  return (
    <div className="space-y-4">
      <form onSubmit={add} className="grid grid-cols-4 gap-2">
        <input className="border rounded px-2 py-1" placeholder="Name"
          value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        <input className="border rounded px-2 py-1" placeholder="Category"
          value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
        <input className="border rounded px-2 py-1" type="number" placeholder="Price"
          value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required />
        <button className="bg-black text-white rounded">Add</button>
      </form>
      <ul className="divide-y">
        {menu.map((m) => (
          <li key={m.id} className="flex justify-between py-2">
            <span>{m.name} <span className="text-gray-400 text-xs">({m.category})</span></span>
            <span>{m.price}
              <button onClick={() => remove(m.id)} className="ml-3 text-red-600 text-sm">delete</button>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
