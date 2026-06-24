import { NavLink, useNavigate } from "react-router-dom";

const links = [
  { to: "/dashboard", label: "All Orders", end: true },
  { to: "/dashboard/branches", label: "Branches Overview" },
  { to: "/dashboard/add-branch", label: "Add New Branch" },
  { to: "/dashboard/settings", label: "Settings" },
];

export default function Sidebar() {
  const nav = useNavigate();
  const logout = () => {
    localStorage.removeItem("token");
    nav("/login");
  };
  return (
    <aside className="w-60 bg-gray-900 text-gray-100 min-h-screen p-4 flex flex-col">
      <h2 className="text-xl font-bold mb-6">🍔 OMS Central</h2>
      <nav className="flex flex-col gap-1 flex-1">
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}
            className={({ isActive }) =>
              `px-3 py-2 rounded ${isActive ? "bg-gray-700" : "hover:bg-gray-800"}`}>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <button onClick={logout}
        className="mt-4 px-3 py-2 rounded bg-red-600 hover:bg-red-700">
        Logout
      </button>
    </aside>
  );
}
