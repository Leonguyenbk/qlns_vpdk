import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../auth/AuthContext";
import { loginSchema } from "../schemas";
import { apiErrorMessage } from "../lib/api";
import { Button, FormField, TextInput } from "../components/ui/primitives";

export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/";

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(loginSchema) });

  if (!loading && isAuthenticated) return <Navigate to={from} replace />;

  const onSubmit = async (values) => {
    try {
      await login(values.username, values.password);
      toast.success("Đăng nhập thành công");
      navigate(from, { replace: true });
    } catch (err) {
      toast.error(apiErrorMessage(err, "Đăng nhập thất bại"));
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-700 to-brand-900 p-4">
      <div className="card w-full max-w-md p-8">
        <div className="mb-6 text-center">
          <div className="text-4xl">🗂️</div>
          <h1 className="mt-2 text-xl font-semibold text-slate-800">Hệ thống quản lý nhân sự</h1>
          <p className="text-sm text-slate-500">Đăng nhập để tiếp tục</p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            label="Tên đăng nhập"
            htmlFor="login-username"
            required
            error={errors.username?.message}
          >
            <TextInput
              id="login-username"
              autoComplete="username"
              autoFocus
              {...register("username")}
              error={errors.username}
            />
          </FormField>
          <FormField
            label="Mật khẩu"
            htmlFor="login-password"
            required
            error={errors.password?.message}
          >
            <TextInput
              id="login-password"
              type="password"
              autoComplete="current-password"
              {...register("password")}
              error={errors.password}
            />
          </FormField>
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Đang đăng nhập..." : "Đăng nhập"}
          </Button>
        </form>
      </div>
    </div>
  );
}
