import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { PERMISSIONS, MODULE_PERMS } from "./lib/constants";

import LoginPage from "./pages/LoginPage";
import LogoutPage from "./pages/LogoutPage";
import PortalPage from "./pages/PortalPage";
import ChangePasswordPage from "./pages/ChangePasswordPage";
import DashboardPage from "./pages/DashboardPage";
import EmployeeListPage from "./pages/employees/EmployeeListPage";
import EmployeeCreatePage from "./pages/employees/EmployeeCreatePage";
import EmployeeDetailPage from "./pages/employees/EmployeeDetailPage";
import EmployeeEditPage from "./pages/employees/EmployeeEditPage";
import EmployeeTransferPage from "./pages/employees/EmployeeTransferPage";
import EmployeeHistoryPage from "./pages/employees/EmployeeHistoryPage";
import UnitTreePage from "./pages/units/UnitTreePage";
import PositionsPage from "./pages/positions/PositionsPage";
import UsersPage from "./pages/users/UsersPage";
import RolesPage from "./pages/roles/RolesPage";
import AuditLogPage from "./pages/audit/AuditLogPage";
import AdminPage, { AdminIndexRedirect } from "./pages/admin/AdminPage";
import GoisoBranchesPage from "./pages/admin/goiso/BranchesPage";
import GoisoBranchConfigPage from "./pages/admin/goiso/BranchConfigPage";
import GoisoStatsPage from "./pages/admin/goiso/StatsPage";
import GoisoDevicesPage from "./pages/admin/goiso/DevicesPage";
import ForbiddenPage from "./pages/ForbiddenPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/logout" element={<LogoutPage />} />

      {/* Cổng ứng dụng — trang đầu sau đăng nhập */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <PortalPage />
          </ProtectedRoute>
        }
      />

      {/* Module Nhân sự + Quản trị hệ thống — trong khung Layout */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route
          path="nhan-su"
          element={
            <ProtectedRoute anyOf={MODULE_PERMS.NHANSU}>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route path="doi-mat-khau" element={<ChangePasswordPage />} />

        <Route
          path="employees"
          element={
            <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_VIEW}>
              <EmployeeListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="employees/new"
          element={
            <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_CREATE}>
              <EmployeeCreatePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="employees/:id"
          element={
            <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_VIEW}>
              <EmployeeDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="employees/:id/edit"
          element={
            <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_UPDATE}>
              <EmployeeEditPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="employees/:id/transfer"
          element={
            <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_TRANSFER}>
              <EmployeeTransferPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="employees/:id/history"
          element={
            <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_VIEW}>
              <EmployeeHistoryPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="units"
          element={
            <ProtectedRoute permission={PERMISSIONS.UNIT_VIEW}>
              <UnitTreePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="positions"
          element={
            <ProtectedRoute permission={PERMISSIONS.POSITION_VIEW}>
              <PositionsPage />
            </ProtectedRoute>
          }
        />
        {/* Quản trị — MỘT trang duy nhất, có tab; mở rộng bằng cách thêm route con */}
        <Route
          path="admin"
          element={
            <ProtectedRoute
              anyOf={[
                PERMISSIONS.USER_VIEW,
                PERMISSIONS.ROLE_VIEW,
                PERMISSIONS.AUDIT_VIEW,
                PERMISSIONS.GOISO_ADMIN,
                PERMISSIONS.GOISO_VIEW,
              ]}
            >
              <AdminPage />
            </ProtectedRoute>
          }
        >
          <Route index element={<AdminIndexRedirect />} />
          <Route
            path="users"
            element={
              <ProtectedRoute permission={PERMISSIONS.USER_VIEW}>
                <UsersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="roles"
            element={
              <ProtectedRoute permission={PERMISSIONS.ROLE_VIEW}>
                <RolesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="audit-logs"
            element={
              <ProtectedRoute permission={PERMISSIONS.AUDIT_VIEW}>
                <AuditLogPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="goiso/branches"
            element={
              <ProtectedRoute permission={PERMISSIONS.GOISO_ADMIN}>
                <GoisoBranchesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="goiso/branches/:code"
            element={
              <ProtectedRoute permission={PERMISSIONS.GOISO_ADMIN}>
                <GoisoBranchConfigPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="goiso/stats"
            element={
              <ProtectedRoute anyOf={[PERMISSIONS.GOISO_ADMIN, PERMISSIONS.GOISO_VIEW]}>
                <GoisoStatsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="goiso/devices"
            element={
              <ProtectedRoute permission={PERMISSIONS.GOISO_ADMIN}>
                <GoisoDevicesPage />
              </ProtectedRoute>
            }
          />
        </Route>
        {/* Đường cũ — chuyển tiếp cho ai còn lưu link */}
        <Route path="users" element={<Navigate to="/admin/users" replace />} />
        <Route path="roles" element={<Navigate to="/admin/roles" replace />} />
        <Route path="audit-logs" element={<Navigate to="/admin/audit-logs" replace />} />

        <Route path="403" element={<ForbiddenPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
