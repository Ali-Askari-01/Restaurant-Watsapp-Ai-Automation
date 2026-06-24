import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api.js";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const { data } = await api.post("/auth/login", { email, password });
      localStorage.setItem("token", data.access_token);
      nav("/dashboard");
    } catch (e) {
      if (!e.response) {
        setErr("Cannot reach API — is the backend running on port 8000?");
      } else {
        setErr("Invalid credentials");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={submit} className="bg-white p-8 rounded-xl shadow w-96 space-y-4">
        <h1 className="text-2xl font-bold text-center">Owner Dashboard</h1>
        <p className="text-xs text-gray-500 text-center">
          Demo: owner@burgerpalace.com / admin123
        </p>
        {err && <p className="text-red-600 text-sm text-center">{err}</p>}
        <input className="w-full border rounded px-3 py-2" placeholder="Email"
               value={email} onChange={(e) => setEmail(e.target.value)} />
        <input className="w-full border rounded px-3 py-2" type="password"
               placeholder="Password" value={password}
               onChange={(e) => setPassword(e.target.value)} />
        <button className="w-full bg-black text-white rounded py-2 hover:bg-gray-800">
          Sign In
        </button>
      </form>
    </div>
  );
}
