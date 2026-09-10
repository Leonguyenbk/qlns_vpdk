import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { PERMISSIONS } from "./lib/constants";

import LoginPage from "./pages/LoginPage";
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
import ForbiddenPage from "./pages/ForbiddenPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route
          index
          element={
            <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_VIEW}>
              <DashboardPage />
            </ProtectedRoute>
          }
        />

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

        <Route path="403" element={<ForbiddenPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
