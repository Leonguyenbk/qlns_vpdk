import { Link, useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { useEmployee, useEmployeeMutations } from "../../hooks/useEmployees";
import { useCan } from "../../components/Can";
import {
  PERMISSIONS,
  EMPLOYEE_STATUS_LABELS,
  EMPLOYEE_STATUS_BADGE,
  EMPLOYMENT_TYPE_LABELS,
  GENDER_LABELS,
  ASSIGNMENT_TYPE_LABELS,
} from "../../lib/constants";
import { formatDate } from "../../lib/format";
import { apiErrorMessage } from "../../lib/api";
import { PageHeader, Button, Badge, Avatar, Card } from "../../components/ui/primitives";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";

function Row({ label, children }) {
  return (
    <div className="flex justify-between gap-4 border-b border-slate-100 py-2 text-sm last:border-0">
      <span className="text-slate-500">{label}</span>
      <span className="text-right font-medium text-slate-800">{children ?? "—"}</span>
    </div>
  );
}

export default function EmployeeDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { can } = useCan();
  const { data, isLoading, isError, error, refetch } = useEmployee(id, { includeDeleted: true });
  const { restore } = useEmployeeMutations();

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const onRestore = async () => {
    try {
      await restore.mutateAsync(id);
      toast.success("Khôi phục nhân sự thành công");
      refetch();
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Chi tiết nhân sự"
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => navigate("/employees")}>
              Danh sách
            </Button>
            {can(PERMISSIONS.EMPLOYEE_UPDATE) && !data.is_deleted && (
              <Button onClick={() => navigate(`/employees/${id}/edit`)}>Chỉnh sửa</Button>
            )}
            {can(PERMISSIONS.EMPLOYEE_TRANSFER) && !data.is_deleted && (
              <Button variant="secondary" onClick={() => navigate(`/employees/${id}/transfer`)}>
                Chuyển đơn vị
              </Button>
            )}
            {can(PERMISSIONS.EMPLOYEE_RESTORE) && data.is_deleted && (
              <Button onClick={onRestore} disabled={restore.isPending}>
                Khôi phục
              </Button>
            )}
          </div>
        }
      />

      {data.is_deleted && (
        <div className="mb-4 rounded-lg bg-amber-50 px-4 py-2 text-sm text-amber-700">
          Nhân sự này đã bị xóa mềm ngày {formatDate(data.deleted_at)}.
        </div>
      )}

      <Card className="mb-4 flex items-center gap-4">
        <Avatar name={data.full_name} url={data.avatar_url} size={64} />
        <div>
          <h2 className="text-lg font-semibold text-slate-800">{data.full_name}</h2>
          <p className="text-sm text-slate-500">
            {data.employee_code} ·{" "}
            <Badge className={EMPLOYEE_STATUS_BADGE[data.status]}>
              {EMPLOYEE_STATUS_LABELS[data.status]}
            </Badge>
          </p>
          <p className="mt-1 text-sm text-slate-600">
            {data.current_unit?.path || data.current_unit?.name || "Chưa phân công"}
            {data.current_position ? ` – ${data.current_position.name}` : ""}
          </p>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <h3 className="mb-2 font-semibold text-slate-800">Thông tin cá nhân</h3>
          <Row label="Ngày sinh">{formatDate(data.date_of_birth)}</Row>
          <Row label="Giới tính">{GENDER_LABELS[data.gender] || "—"}</Row>
          <Row label="Số CCCD">
            {data.identity_number || (data.has_sensitive_data ? "••• (ẩn)" : "—")}
          </Row>
          <Row label="Điện thoại">{data.phone}</Row>
          <Row label="Email">{data.email}</Row>
          <Row label="Địa chỉ">{data.address}</Row>
        </Card>
        <Card>
          <h3 className="mb-2 font-semibold text-slate-800">Thông tin công tác</h3>
          <Row label="Phòng / Chi nhánh">{data.current_unit?.group_name || "—"}</Row>
          <Row label="Bộ phận">{data.current_unit?.section_name || "—"}</Row>
          <Row label="Chức vụ">{data.current_position?.name || "—"}</Row>
          <Row label="Chức danh chuyên môn">{data.professional_title}</Row>
          <Row label="Loại nhân sự">{EMPLOYMENT_TYPE_LABELS[data.employment_type] || "—"}</Row>
          <Row label="Ngày tuyển dụng">{formatDate(data.recruitment_date)}</Row>
          <Row label="Cập nhật lần cuối">{formatDate(data.updated_at)}</Row>
        </Card>
      </div>

      <Card className="mt-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-semibold text-slate-800">Quá trình công tác</h3>
          <Link to={`/employees/${id}/history`} className="text-sm text-brand-600 hover:underline">
            Xem đầy đủ →
          </Link>
        </div>
        <ul className="divide-y divide-slate-100 text-sm">
          {(data.assignments || []).slice(0, 5).map((a) => (
            <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
              <span>
                <span className="font-medium text-slate-800">{a.unit?.path || a.unit?.name}</span> ·{" "}
                {a.position?.name}{" "}
                <Badge className="ml-1 bg-slate-100 text-slate-600">
                  {ASSIGNMENT_TYPE_LABELS[a.assignment_type] || a.assignment_type}
                </Badge>
              </span>
              <span className="text-slate-400">
                {formatDate(a.start_date)} – {a.end_date ? formatDate(a.end_date) : "nay"}
                {a.is_active && a.is_primary && (
                  <Badge className="ml-2 bg-green-100 text-green-700">Hiện tại</Badge>
                )}
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
