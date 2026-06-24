import { useState } from "react";
import api from "../api/api.js";

const STATUSES = ["pending", "confirmed", "preparing", "delivered", "cancelled"];

export default function OrderModal({ order, onClose, onUpdated }) {
  const [status, setStatus] = useState(order.status);
  const [saving, setSaving] = useState(false);
  if (!order) return null;

  const items = Array.isArray(order.items) ? order.items : [];

  const save = async () => {
    setSaving(true);
    try {
      await api.patch(
        `/tenant/${order.tenant_id}/orders/${order.order_id}/status`,
        { status }
      );
      onUpdated();
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-lg p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold">Order Detail</h2>
          <button onClick={onClose} className="text-gray-400 text-2xl">&times;</button>
        </div>
        <div className="text-sm space-y-1">
          <p><b>Branch:</b> {order.tenant_name} — {order.branch_location}</p>
          <p><b>Customer:</b> {order.customer_name}</p>
          <p><b>Phone:</b> {order.customer_phone}</p>
          {order.delivery_address && <p><b>Address:</b> {order.delivery_address}</p>}
          <p><b>Placed:</b> {new Date(order.created_at).toLocaleString()}</p>
        </div>
        {items.length > 0 && (
          <table className="w-full text-sm border-t">
            <thead><tr className="text-left text-gray-500">
              <th className="py-1">Item</th><th>Qty</th><th>Price</th>
            </tr></thead>
            <tbody>
              {items.map((it, i) => (
                <tr key={i} className="border-t">
                  <td className="py-1">{it.name}</td><td>{it.qty}</td><td>{it.price}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="font-bold text-right">Total: {order.total_price}</p>
        <div className="flex items-center gap-3">
          <select value={status} onChange={(e) => setStatus(e.target.value)}
                  className="border rounded px-3 py-2 flex-1">
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <button onClick={save} disabled={saving}
                  className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">
            {saving ? "Saving…" : "Update Status"}
          </button>
        </div>
      </div>
    </div>
  );
}
