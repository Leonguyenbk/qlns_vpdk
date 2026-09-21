import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { PERMISSIONS, MODULE_PERMS } from "./lib/constants";

import LoginPage from "./pages/LoginPage";
import LogoutPage from "./pages/LogoutPage";
import OverviewPage from "./pages/OverviewPage";
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
import PeriodsPage from "./pages/admin/kpi/PeriodsPage";
import PeriodScoresPage from "./pages/admin/kpi/PeriodScoresPage";
import CriteriaSetsPage from "./pages/admin/kpi/CriteriaSetsPage";
import ProductsPage from "./pages/admin/kpi/ProductsPage";
import ForbiddenPage from "./pages/ForbiddenPage";
import NotFoundPage from "./pages/NotFoundPage";

import ExecutiveDashboardPage from "./pages/tasks/ExecutiveDashboardPage";
import TaskListPage from "./pages/tasks/TaskListPage";
import TaskDetailPage from "./pages/tasks/TaskDetailPage";
import TaskCreatePage from "./pages/tasks/TaskCreatePage";
import MyKpiPage from "./pages/kpi/MyKpiPage";
import KpiScoreDetailPage from "./pages/kpi/KpiScoreDetailPage";
import WorkPage, { WorkIndexRedirect } from "./pages/work/WorkPage";
import HrPage, { LegacyEmployeeRedirect } from "./pages/hr/HrPage";

import BranchPickerPage from "./pages/goiso/BranchPickerPage";
import BoardPage from "./pages/goiso/BoardPage";
import DisplayPage from "./pages/goiso/DisplayPage";
import DisplaySimplePage from "./pages/goiso/DisplaySimplePage";
import ScreensPickPage from "./pages/goiso/ScreensPickPage";
import CounterPage from "./pages/goiso/CounterPage";
import BookingPage from "./pages/goiso/BookingPage";
import BookingLookupPage from "./pages/goiso/BookingLookupPage";

import SurveyListPage from "./pages/surveys/SurveyListPage";
import SurveyEditPage from "./pages/surveys/SurveyEditPage";
import SurveyQuestionsPage from "./pages/surveys/SurveyQuestionsPage";
import SurveyResponsesPage from "./pages/surveys/SurveyResponsesPage";
import SurveyStatisticsPage from "./pages/surveys/SurveyStatisticsPage";
import SurveyResultsHubPage from "./pages/surveys/SurveyResultsHubPage";
import SurveyStatisticsHubPage from "./pages/surveys/SurveyStatisticsHubPage";
import PublicSurveyPage from "./pages/public/PublicSurveyPage";
import QrGeneratorPage from "./pages/public/QrGeneratorPage";

const GOISO_STAFF = [PERMISSIONS.GOISO_COUNTER, PERMISSIONS.GOISO_ADMIN];

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/logout" element={<LogoutPage />} />

      {/* Gọi số — trang toàn màn hình riêng, KHÔNG dùng khung Layout (sidebar) */}
      <Route path="/cho" element={<BranchPickerPage />} />
      <Route path="/b/:code/cho" element={<BoardPage />} />
      <Route path="/dat-lich" element={<BookingPage />} />
      <Route path="/lich-hen/:token" element={<BookingLookupPage />} />

      {/* Khảo sát – Đánh giá mức độ hài lòng: trang công khai cho người dân, không cần đăng nhập */}
      <Route path="/khao-sat/:slug" element={<PublicSurveyPage />} />
      <Route path="/tao-ma-qr" element={<QrGeneratorPage />} />
      <Route
        path="/b/:code/counter"
        element={
          <ProtectedRoute anyOf={GOISO_STAFF}>
            <CounterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/b/:code/man-hinh"
        element={
          <ProtectedRoute anyOf={GOISO_STAFF}>
            <ScreensPickPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/b/:code/display"
        element={
          <ProtectedRoute anyOf={GOISO_STAFF}>
            <DisplayPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/b/:code/display/simple"
        element={
          <ProtectedRoute anyOf={GOISO_STAFF}>
            <DisplaySimplePage />
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
          index
          element={
            <ProtectedRoute permission={PERMISSIONS.ANNOUNCEMENT_VIEW}>
              <OverviewPage />
            </ProtectedRoute>
          }
        />
        <Route path="doi-mat-khau" element={<ChangePasswordPage />} />

        {/* Nhân sự — MỘT trang duy nhất, có tab (Tổng quan, Danh sách, Cơ cấu, Chức vụ) */}
        <Route
          path="nhan-su"
          element={
            <ProtectedRoute anyOf={MODULE_PERMS.NHANSU}>
              <HrPage />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route
            path="nhan-vien"
            element={
              <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_VIEW}>
                <EmployeeListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="nhan-vien/new"
            element={
              <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_CREATE}>
                <EmployeeCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="nhan-vien/:id"
            element={
              <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_VIEW}>
                <EmployeeDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="nhan-vien/:id/edit"
            element={
              <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_UPDATE}>
                <EmployeeEditPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="nhan-vien/:id/transfer"
            element={
              <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_TRANSFER}>
                <EmployeeTransferPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="nhan-vien/:id/history"
            element={
              <ProtectedRoute permission={PERMISSIONS.EMPLOYEE_VIEW}>
                <EmployeeHistoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="co-cau"
            element={
              <ProtectedRoute permission={PERMISSIONS.UNIT_VIEW}>
                <UnitTreePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="chuc-vu"
            element={
              <ProtectedRoute permission={PERMISSIONS.POSITION_VIEW}>
                <PositionsPage />
              </ProtectedRoute>
            }
          />
        </Route>
        {/* Đường cũ — chuyển tiếp cho ai còn lưu link */}
        <Route path="employees/*" element={<LegacyEmployeeRedirect />} />
        <Route path="units" element={<Navigate to="/nhan-su/co-cau" replace />} />
        <Route path="positions" element={<Navigate to="/nhan-su/chuc-vu" replace />} />

        {/* Khảo sát – Đánh giá mức độ hài lòng */}
        <Route
          path="surveys"
          element={
            <ProtectedRoute permission={PERMISSIONS.SURVEY_VIEW}>
              <SurveyListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="surveys/new"
          element={
            <ProtectedRoute permission={PERMISSIONS.SURVEY_CREATE}>
              <SurveyEditPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="surveys/results"
          element={
            <ProtectedRoute permission={PERMISSIONS.SURVEY_VIEW_STATISTICS}>
              <SurveyResultsHubPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="surveys/statistics"
          element={
            <ProtectedRoute permission={PERMISSIONS.SURVEY_VIEW_STATISTICS}>
              <SurveyStatisticsHubPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="surveys/:id"
          element={
            <ProtectedRoute permission={PERMISSIONS.SURVEY_VIEW}>
              <SurveyEditPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="surveys/:id/questions"
          element={
            <ProtectedRoute permission={PERMISSIONS.SURVEY_VIEW}>
              <SurveyQuestionsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="surveys/:id/responses"
          element={
            <ProtectedRoute permission={PERMISSIONS.SURVEY_VIEW_STATISTICS}>
              <SurveyResponsesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="surveys/:id/statistics"
          element={
            <ProtectedRoute permission={PERMISSIONS.SURVEY_VIEW_STATISTICS}>
              <SurveyStatisticsPage />
            </ProtectedRoute>
          }
        />

        {/* Công việc — MỘT trang duy nhất, có tab (Giao việc + KPI); mở rộng bằng cách thêm route con */}
        <Route
          path="cong-viec"
          element={
            <ProtectedRoute anyOf={MODULE_PERMS.WORK}>
              <WorkPage />
            </ProtectedRoute>
          }
        >
          <Route index element={<WorkIndexRedirect />} />
          <Route
            path="tong-quan"
            element={
              <ProtectedRoute permission={PERMISSIONS.TASK_VIEW_ALL}>
                <ExecutiveDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="danh-sach"
            element={
              <ProtectedRoute anyOf={[PERMISSIONS.TASK_VIEW_ALL, PERMISSIONS.TASK_VIEW_OWN]}>
                <TaskListPage mode="all" />
              </ProtectedRoute>
            }
          />
          <Route
            path="danh-sach/moi"
            element={
              <ProtectedRoute permission={PERMISSIONS.TASK_CREATE}>
                <TaskCreatePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="danh-sach/:id"
            element={
              <ProtectedRoute anyOf={[PERMISSIONS.TASK_VIEW_ALL, PERMISSIONS.TASK_VIEW_OWN]}>
                <TaskDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="cua-toi"
            element={
              <ProtectedRoute permission={PERMISSIONS.TASK_VIEW_OWN}>
                <TaskListPage mode="mine" />
              </ProtectedRoute>
            }
          />
          <Route
            path="da-giao"
            element={
              <ProtectedRoute anyOf={[PERMISSIONS.TASK_CREATE, PERMISSIONS.TASK_ASSIGN]}>
                <TaskListPage mode="assigned" />
              </ProtectedRoute>
            }
          />
          <Route
            path="kpi"
            element={
              <ProtectedRoute permission={PERMISSIONS.KPI_VIEW_OWN}>
                <MyKpiPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="kpi/:id"
            element={
              <ProtectedRoute anyOf={[PERMISSIONS.KPI_VIEW_OWN, PERMISSIONS.KPI_VIEW_ALL]}>
                <KpiScoreDetailPage />
              </ProtectedRoute>
            }
          />
        </Route>

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
                PERMISSIONS.KPI_PERIOD_MANAGE,
                PERMISSIONS.KPI_CRITERIA_MANAGE,
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
          <Route
            path="kpi/ky-danh-gia"
            element={
              <ProtectedRoute permission={PERMISSIONS.KPI_PERIOD_MANAGE}>
                <PeriodsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="kpi/ky-danh-gia/:periodId"
            element={
              <ProtectedRoute permission={PERMISSIONS.KPI_VIEW_ALL}>
                <PeriodScoresPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="kpi/bo-tieu-chi"
            element={
              <ProtectedRoute permission={PERMISSIONS.KPI_CRITERIA_MANAGE}>
                <CriteriaSetsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="kpi/danh-muc-san-pham"
            element={
              <ProtectedRoute permission={PERMISSIONS.KPI_CRITERIA_MANAGE}>
                <ProductsPage />
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
