export default function BranchCard({ s }) {
  return (
    <div className="bg-white rounded-xl shadow p-5 border">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-bold text-lg">{s.name}</h3>
          <p className="text-sm text-gray-500">{s.branch_location}</p>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${
          s.is_active ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-600"}`}>
          {s.is_active ? "Active" : "Inactive"}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
        <Stat label="Orders Today" value={s.orders_today} />
        <Stat label="Revenue Today" value={Number(s.revenue_today).toLocaleString()} />
        <Stat label="All-Time Orders" value={s.orders_all_time} />
        <Stat label="All-Time Revenue" value={Number(s.revenue_all_time).toLocaleString()} />
      </div>
      <p className="text-xs text-gray-400 mt-3">
        Last order: {s.last_order_at ? new Date(s.last_order_at).toLocaleString() : "—"}
      </p>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-gray-50 rounded p-2">
      <p className="text-gray-500">{label}</p>
      <p className="font-semibold text-base">{value}</p>
    </div>
  );
}
