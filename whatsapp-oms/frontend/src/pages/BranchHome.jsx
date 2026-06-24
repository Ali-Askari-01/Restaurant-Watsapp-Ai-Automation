import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../api/api.js";

export default function BranchHome() {
  const { tenantId } = useParams();
  const [tenant, setTenant] = useState(null);

  useEffect(() => {
    api.get(`/tenant/${tenantId}/menu`).catch(() => {});
    setTenant({ tenantId });
  }, [tenantId]);

  const waLink = `https://wa.me/?text=${encodeURIComponent(
    `Hi! I'd like to order from your ${tenantId} branch.`
  )}`;

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 to-white">
      <div className="max-w-3xl mx-auto px-6 py-16 text-center">
        <div className="text-6xl mb-4">🍔</div>
        <h1 className="text-4xl font-bold capitalize">
          {tenantId.replaceAll("_", " ")}
        </h1>
        <p className="text-gray-500 mt-2">Fresh, fast & delicious — order in seconds.</p>
        <div className="flex gap-3 justify-center mt-8">
          <Link to={`/branch/${tenantId}/menu`}
            className="bg-black text-white px-6 py-3 rounded-lg">View Menu</Link>
          <a href={waLink} target="_blank" rel="noreferrer"
            className="bg-green-600 text-white px-6 py-3 rounded-lg">Order via WhatsApp</a>
          <Link to={`/branch/${tenantId}/track`}
            className="border px-6 py-3 rounded-lg">Track Order</Link>
        </div>
      </div>
    </div>
  );
}
