import { useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { BASE_URL } from "../api/api.js";

export default function OrderTracker() {
  const { tenantId } = useParams();
  const [phone, setPhone] = useState("");
  const [order, setOrder] = useState(null);
  const [err, setErr] = useState("");

  const lookup = async (e) => {
    e.preventDefault();
    setErr(""); setOrder(null);
    try {
      const { data } = await axios.get(`${BASE_URL}/tenant/${tenantId}/track`, {
        params: { phone },
      });
      if (!data) setErr("No order found for this number.");
      else setOrder(data);
    } catch {
      setErr("Could not look up order. Please try again.");
    }
  };

  return (
    <div className="max-w-md mx-auto px-6 py-12">
      <h1 className="text-2xl font-bold mb-4">Track Your Order</h1>
      <form onSubmit={lookup} className="flex gap-2">
        <input className="border rounded px-3 py-2 flex-1" placeholder="Your phone number"
          value={phone} onChange={(e) => setPhone(e.target.value)} />
        <button className="bg-black text-white px-4 rounded">Track</button>
      </form>
      {err && <p className="text-red-600 mt-3 text-sm">{err}</p>}
      {order && (
        <div className="mt-6 bg-white shadow rounded p-4">
          <p className="text-lg font-semibold capitalize">Status: {order.status}</p>
          <p className="text-sm text-gray-500">Total: {order.total_price}</p>
          <p className="text-xs text-gray-400">
            Placed: {new Date(order.created_at).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}
