const badge = {
  pending: "bg-yellow-100 text-yellow-700",
  confirmed: "bg-blue-100 text-blue-700",
  preparing: "bg-purple-100 text-purple-700",
  delivered: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
};

export default function OrderTable({ orders, onRowClick }) {
  return (
    <div className="bg-white rounded-xl shadow overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-left text-gray-500">
          <tr>
            <th className="p-3">Branch</th><th>Customer</th><th>Phone</th>
            <th>Total</th><th>Status</th><th>Placed</th>
          </tr>
        </thead>
        <tbody>
          {orders.length === 0 && (
            <tr><td colSpan="6" className="p-6 text-center text-gray-400">No orders</td></tr>
          )}
          {orders.map((o) => (
            <tr key={o.order_id} onClick={() => onRowClick(o)}
                className="border-t hover:bg-gray-50 cursor-pointer">
              <td className="p-3">{o.tenant_name}<br/>
                <span className="text-xs text-gray-400">{o.branch_location}</span></td>
              <td>{o.customer_name}</td>
              <td>{o.customer_phone}</td>
              <td>{o.total_price}</td>
              <td><span className={`text-xs px-2 py-1 rounded-full ${badge[o.status] || ""}`}>
                {o.status}</span></td>
              <td>{new Date(o.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
