import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../api/api.js";

export default function BranchMenu() {
  const { tenantId } = useParams();
  const [menu, setMenu] = useState([]);

  useEffect(() => {
    api.get(`/tenant/${tenantId}/menu`).then((r) => setMenu(r.data));
  }, [tenantId]);

  const grouped = menu.reduce((acc, m) => {
    (acc[m.category || "Other"] ||= []).push(m);
    return acc;
  }, {});

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <Link to={`/branch/${tenantId}`} className="text-sm text-gray-500">&larr; Back</Link>
      <h1 className="text-3xl font-bold my-4">Menu</h1>
      {Object.entries(grouped).map(([cat, items]) => (
        <div key={cat} className="mb-8">
          <h2 className="text-xl font-semibold border-b pb-1 mb-3">{cat}</h2>
          <ul className="space-y-2">
            {items.map((m) => (
              <li key={m.id} className="flex justify-between">
                <div>
                  <p className="font-medium">{m.name}</p>
                  <p className="text-sm text-gray-500">{m.description}</p>
                </div>
                <span className="font-semibold">{m.price}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
