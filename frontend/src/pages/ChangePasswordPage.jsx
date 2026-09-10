import { useState } from "react";
import toast from "react-hot-toast";
import { useAuth } from "../auth/AuthContext";
import { api, apiErrorMessage } from "../lib/api";

export default function ChangePasswordPage() {
  const { logout } = useAuth();
  const [form, setForm] = useState({ old_password: "", new_password: "", confirm: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    if (form.new_password.length < 8) return setErr("Mật khẩu mới phải có ít nhất 8 ký tự.");
    if (form.new_password !== form.confirm) return setErr("Xác nhận mật khẩu không khớp.");
    setBusy(true);
    try {
      await api.put("/auth/change-password", {
        old_password: form.old_password,
        new_password: form.new_password,
      });
      toast.success("Đổi mật khẩu thành công. Vui lòng đăng nhập lại.");
      await logout();
      window.location.href = "/login";
    } catch (e2) {
      setErr(apiErrorMessage(e2, "Không đổi được mật khẩu."));
    } finally {
      setBusy(false);
    }
  };

  const input =
    "w-full rounded-[10px] border border-[#e5e7eb] bg-white px-3 py-2.5 text-sm outline-none " +
    "focus:border-[#7c3aed] focus:ring-4 focus:ring-[#7c3aed]/15";

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-xl font-bold text-ink">Đổi mật khẩu</h1>
      <form onSubmit={onSubmit} className="card mt-5 space-y-4 p-6">
        <div>
          <label className="mb-1 block text-sm font-medium text-ink-2">Mật khẩu hiện tại</label>
          <input type="password" autoComplete="current-password" className={input}
            value={form.old_password} onChange={set("old_password")} required />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-ink-2">Mật khẩu mới</label>
          <input type="password" autoComplete="new-password" className={input}
            value={form.new_password} onChange={set("new_password")} required />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-ink-2">Xác nhận mật khẩu mới</label>
          <input type="password" autoComplete="new-password" className={input}
            value={form.confirm} onChange={set("confirm")} required />
        </div>
        {err && (
          <p className="rounded-[10px] border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {err}
          </p>
        )}
        <button type="submit" disabled={busy}
          className="btn-primary w-full justify-center disabled:opacity-60">
          {busy ? "Đang lưu…" : "Đổi mật khẩu"}
        </button>
      </form>
    </div>
  );
}
