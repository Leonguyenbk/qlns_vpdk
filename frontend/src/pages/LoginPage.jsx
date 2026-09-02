import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../auth/AuthContext";
import { loginSchema } from "../schemas";
import { apiErrorMessage } from "../lib/api";
import { IconUser, IconLock, IconEye, IconEyeOff } from "../components/ui/icons";

const REMEMBER_KEY = "qlns:remembered_username";
// Gradient dùng lại ở panel phải + header mobile + nút submit.
const PANEL_GRADIENT = "linear-gradient(135deg,#1d4ed8 0%,#6d28d9 55%,#9333ea 100%)";
const BUTTON_GRADIENT = "linear-gradient(135deg,#2563eb 0%,#9333ea 100%)";

export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/";

  const [showPw, setShowPw] = useState(false);
  const [remember, setRemember] = useState(false);
  const [formError, setFormError] = useState("");

  const {
    register,
    handleSubmit,
    setValue,
    setFocus,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(loginSchema) });

  // Prefill tên đăng nhập nếu đã chọn "ghi nhớ" trước đó (chỉ localStorage, không đụng token).
  useEffect(() => {
    try {
      const saved = localStorage.getItem(REMEMBER_KEY);
      if (saved) {
        setValue("username", saved);
        setRemember(true);
        setFocus("password");
        return;
      }
    } catch {
      /* localStorage bị chặn — bỏ qua */
    }
    setFocus("username");
  }, [setValue, setFocus]);

  if (!loading && isAuthenticated) return <Navigate to={from} replace />;

  const onSubmit = async (values) => {
    setFormError("");
    try {
      await login(values.username, values.password);
      try {
        if (remember) localStorage.setItem(REMEMBER_KEY, values.username);
        else localStorage.removeItem(REMEMBER_KEY);
      } catch {
        /* bỏ qua nếu localStorage không dùng được */
      }
      toast.success("Đăng nhập thành công");
      navigate(from, { replace: true });
    } catch (err) {
      setFormError(apiErrorMessage(err, "Tên đăng nhập hoặc mật khẩu không đúng."));
    }
  };

  const onForgot = () =>
    toast("Liên hệ quản trị viên đơn vị của bạn để được cấp lại mật khẩu.", { duration: 5000 });

  const inputBase =
    "w-full rounded-[10px] border border-[#e5e7eb] bg-white py-2.5 text-sm text-gray-800 " +
    "placeholder:text-gray-400 outline-none transition-[border-color,box-shadow] duration-200 " +
    "focus:border-[#7c3aed] focus:ring-4 focus:ring-[#7c3aed]/15 " +
    "aria-[invalid=true]:border-red-400 aria-[invalid=true]:focus:ring-red-200";

  return (
    <div
      className="flex min-h-screen w-full items-center justify-center p-4"
      style={{
        backgroundColor: "#f3f4f6",
        backgroundImage:
          "radial-gradient(900px 500px at 50% -5%, #eef2ff 0%, transparent 70%)",
      }}
    >
      <div className="flex w-full max-w-[940px] flex-col overflow-hidden rounded-[20px] bg-white shadow-[0_24px_70px_-24px_rgba(30,41,59,0.35)] lg:min-h-[520px] lg:flex-row">
        {/* ── Header gradient (chỉ mobile) ── */}
        <div
          className="px-8 py-7 text-white lg:hidden"
          style={{ backgroundImage: PANEL_GRADIENT }}
        >
          <div className="mx-auto w-full max-w-md">
            <div className="flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/15 text-xs font-bold tracking-wide ring-1 ring-white/25">
                NS
              </span>
              <span className="text-sm font-semibold">Quản lý nhân sự</span>
            </div>
            <h2 className="mt-4 text-2xl font-extrabold leading-tight">Chào mừng trở lại!</h2>
            <p className="mt-1 text-sm text-white/85">
              Đăng nhập để truy cập và quản lý hệ thống.
            </p>
          </div>
        </div>

        {/* ── Form (trái) ── */}
        <div className="flex w-full flex-col justify-center px-8 py-10 sm:px-12 lg:w-[56%] lg:px-14 lg:py-12">
          <div className="mx-auto w-full max-w-md lg:max-w-none">
            <h1 className="text-3xl font-bold tracking-tight text-gray-900">Đăng nhập</h1>
            <p className="mt-2 text-sm text-gray-500">
              Đăng nhập để tiếp tục sử dụng hệ thống
            </p>

            <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-4" noValidate>
            {/* Tên đăng nhập */}
            <div>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex w-11 items-center justify-center text-gray-400">
                  <IconUser size={18} />
                </span>
                <input
                  id="login-username"
                  type="text"
                  autoComplete="username"
                  placeholder="Tên đăng nhập"
                  aria-invalid={errors.username ? "true" : undefined}
                  className={`${inputBase} pl-11 pr-3.5`}
                  {...register("username")}
                />
              </div>
              {errors.username && (
                <p className="mt-1 text-xs text-red-600">{errors.username.message}</p>
              )}
            </div>

            {/* Mật khẩu */}
            <div>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex w-11 items-center justify-center text-gray-400">
                  <IconLock size={18} />
                </span>
                <input
                  id="login-password"
                  type={showPw ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="Mật khẩu"
                  aria-invalid={errors.password ? "true" : undefined}
                  className={`${inputBase} pl-11 pr-11`}
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => !s)}
                  aria-pressed={showPw}
                  aria-label={showPw ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  title={showPw ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  className="absolute inset-y-0 right-0 flex w-11 cursor-pointer items-center justify-center text-gray-400 transition-colors hover:text-gray-600 focus-visible:text-[#7c3aed] focus-visible:outline-none"
                >
                  {showPw ? <IconEyeOff size={18} /> : <IconEye size={18} />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
              )}
            </div>

            {/* Ghi nhớ / Quên mật khẩu */}
            <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
              <label className="flex cursor-pointer select-none items-center gap-2 text-gray-600">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="h-4 w-4 cursor-pointer rounded border-gray-300 accent-[#7c3aed]"
                />
                Ghi nhớ đăng nhập
              </label>
              <button
                type="button"
                onClick={onForgot}
                className="cursor-pointer font-medium text-[#7c3aed] transition-colors hover:text-[#6d28d9] hover:underline"
              >
                Quên mật khẩu?
              </button>
            </div>

            {/* Lỗi đăng nhập */}
            {formError && (
              <div
                role="alert"
                className="rounded-[10px] border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
              >
                {formError}
              </div>
            )}

            {/* Nút submit */}
            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={isSubmitting}
                style={{ backgroundImage: BUTTON_GRADIENT }}
                className="inline-flex min-w-[150px] cursor-pointer items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-semibold uppercase tracking-wide text-white shadow-md shadow-purple-500/20 transition-all duration-200 hover:-translate-y-px hover:shadow-lg hover:shadow-purple-500/30 hover:brightness-110 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#7c3aed]/30 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
              >
                {isSubmitting && (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                )}
                {isSubmitting ? "Đang đăng nhập…" : "Đăng nhập"}
              </button>
            </div>
          </form>
          </div>
        </div>

        {/* ── Panel Welcome (phải, chỉ desktop) ── */}
        <div
          aria-hidden="true"
          className="relative hidden overflow-hidden text-white lg:block lg:w-[44%] lg:[clip-path:polygon(28%_0,100%_0,100%_100%,28%_100%,0_50%)]"
          style={{ backgroundImage: PANEL_GRADIENT }}
        >
          {/* Lớp hình học trang trí */}
          <div className="pointer-events-none absolute -left-20 -top-24 h-72 w-72 rounded-full bg-white/20 blur-3xl" />
          <div className="pointer-events-none absolute right-0 top-0 h-full w-3/4 bg-white/10 [clip-path:polygon(45%_0,100%_0,100%_55%)]" />
          <div className="pointer-events-none absolute -bottom-16 left-0 h-48 w-[150%] -rotate-[16deg] bg-white/10" />
          <div className="pointer-events-none absolute bottom-0 left-0 h-1/2 w-2/3 bg-[#4c1d95]/45 [clip-path:polygon(0_35%,100%_100%,0_100%)]" />
          <div className="pointer-events-none absolute right-8 top-10 h-24 w-24 rotate-45 border border-white/25" />

          {/* Nội dung */}
          <div className="relative flex h-full flex-col justify-between py-14 pl-[26%] pr-12">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/15 text-sm font-bold tracking-wide ring-1 ring-white/25">
                NS
              </span>
              <span className="text-sm font-semibold">Quản lý nhân sự</span>
            </div>

            <div>
              <h2 className="text-[2.6rem] font-extrabold leading-[1.1] [text-shadow:0_2px_24px_rgba(0,0,0,0.18)]">
                Chào mừng
                <br />
                trở lại!
              </h2>
              <p className="mt-4 max-w-[16rem] text-[0.95rem] leading-relaxed text-white/85">
                Đăng nhập để truy cập và quản lý hệ thống.
              </p>
            </div>

            <p className="text-xs uppercase tracking-[0.18em] text-white/55">
              Văn phòng Đăng ký Đất đai
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
