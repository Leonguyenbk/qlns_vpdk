import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useEmployees, useEmployeeMutations } from "../../hooks/useEmployees";
import { useUnits } from "../../hooks/useUnits";
import { usePositions } from "../../hooks/usePositions";
import { useCan } from "../../components/Can";
import { PERMISSIONS, EMPLOYEE_STATUS_LABELS, EMPLOYEE_STATUS_BADGE } from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { PageHeader, Button, Badge, Avatar, TextInput, Select } from "../../components/ui/primitives";
import { Table, Pagination } from "../../components/ui/Table";
import { LoadingState, EmptyState, ErrorState } from "../../components/ui/DataStates";
import { ConfirmDialog } from "../../components/ui/Modal";

const DEFAULT_FILTERS = {
  keyword: "",
  unit_id: "",
  position_id: "",
  status: "",
  page: 1,
  page_size: 10,
  sort: "updated_at",
  order: "desc",
  include_deleted: "",
};

export default function EmployeeListPage() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [pendingDelete, setPendingDelete] = useState(null);
  const navigate = useNavigate();
  const { can } = useCan();

  const params = useMemo(() => {
    const p = { ...filters };
    Object.keys(p).forEach((k) => p[k] === "" && delete p[k]);
    return p;
  }, [filters]);

  const { data, isLoading, isError, error, refetch, isFetching } = useEmployees(params);
  const { data: units } = useUnits({ only_active: true });
  const { data: positions } = usePositions({ only_active: true });
  const { remove, restore } = useEmployeeMutations();

  const setFilter = (patch) => setFilters((f) => ({ ...f, ...patch, page: 1 }));

  const onDelete = async () => {
    try {
      await remove.mutateAsync(pendingDelete.id);
      toast.success("Đã xóa nhân sự (có thể khôi phục)");
      setPendingDelete(null);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onRestore = async (employee) => {
    try {
      await restore.mutateAsync(employee.id);
      toast.success(`Đã khôi phục nhân sự "${employee.full_name}"`);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const columns = [
    {
      key: "employee",
      header: "Nhân sự",
      render: (r) => (
        <div className="flex items-center gap-3">
          <Avatar name={r.full_name} url={r.avatar_url} size={36} />
          <div>
            <Link to={`/employees/${r.id}`} className="font-medium text-brand-700 hover:underline">
              {r.full_name}
            </Link>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span>{r.employee_code}</span>
              {r.is_deleted && <Badge className="bg-red-100 text-red-700">Đã xóa</Badge>}
            </div>
          </div>
        </div>
      ),
    },
    { key: "current_unit", header: "Đơn vị", render: (r) => r.current_unit?.name || "—" },
    { key: "current_position", header: "Chức vụ", render: (r) => r.current_position?.name || "—" },
    {
      key: "status",
      header: "Trạng thái",
      render: (r) => (
        <Badge className={EMPLOYEE_STATUS_BADGE[r.status]}>
          {EMPLOYEE_STATUS_LABELS[r.status] || r.status}
        </Badge>
      ),
    },
    { key: "recruitment_date", header: "Ngày tuyển dụng", render: (r) => formatDate(r.recruitment_date) },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (r) => (
        <div className="flex justify-end gap-1">
          <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => navigate(`/employees/${r.id}`)}>
            Xem
          </Button>
          {can(PERMISSIONS.EMPLOYEE_RESTORE) && r.is_deleted && (
            <Button
              variant="ghost"
              className="px-2 py-1 text-xs text-green-700"
              disabled={restore.isPending}
              onClick={() => onRestore(r)}
            >
              Khôi phục
            </Button>
          )}
          {can(PERMISSIONS.EMPLOYEE_UPDATE) && !r.is_deleted && (
            <Button
              variant="ghost"
              className="px-2 py-1 text-xs"
              onClick={() => navigate(`/employees/${r.id}/edit`)}
            >
              Sửa
            </Button>
          )}
          {can(PERMISSIONS.EMPLOYEE_TRANSFER) && !r.is_deleted && (
            <Button
              variant="ghost"
              className="px-2 py-1 text-xs"
              onClick={() => navigate(`/employees/${r.id}/transfer`)}
            >
              Chuyển
            </Button>
          )}
          {can(PERMISSIONS.EMPLOYEE_DELETE) && !r.is_deleted && (
            <Button
              variant="ghost"
              className="px-2 py-1 text-xs text-red-600"
              onClick={() => setPendingDelete(r)}
            >
              Xóa
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Danh sách nhân sự"
        subtitle="Danh sách được lọc theo phạm vi đơn vị của tài khoản"
        actions={
          can(PERMISSIONS.EMPLOYEE_CREATE) && (
            <Button onClick={() => navigate("/employees/new")}>+ Thêm nhân sự</Button>
          )
        }
      />

      <div className="card mb-4 grid gap-3 p-4 md:grid-cols-3 xl:grid-cols-6">
        <TextInput
          placeholder="Tìm theo mã, họ tên, SĐT..."
          value={filters.keyword}
          onChange={(e) => setFilter({ keyword: e.target.value })}
        />
        <Select value={filters.unit_id} onChange={(e) => setFilter({ unit_id: e.target.value })}>
          <option value="">Tất cả đơn vị</option>
          {units?.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </Select>
        <Select value={filters.position_id} onChange={(e) => setFilter({ position_id: e.target.value })}>
          <option value="">Tất cả chức vụ</option>
          {positions?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </Select>
        <Select value={filters.status} onChange={(e) => setFilter({ status: e.target.value })}>
          <option value="">Tất cả trạng thái</option>
          {Object.entries(EMPLOYEE_STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </Select>
        <Select
          value={filters.include_deleted}
          onChange={(e) => setFilter({ include_deleted: e.target.value })}
          aria-label="Lọc hồ sơ đã xóa"
        >
          <option value="">Chỉ hồ sơ hiện hành</option>
          <option value="true">Bao gồm hồ sơ đã xóa</option>
        </Select>
        <Select
          value={`${filters.sort}:${filters.order}`}
          onChange={(e) => {
            const [sort, order] = e.target.value.split(":");
            setFilter({ sort, order });
          }}
        >
          <option value="updated_at:desc">Mới cập nhật</option>
          <option value="full_name:asc">Tên A→Z</option>
          <option value="full_name:desc">Tên Z→A</option>
          <option value="recruitment_date:desc">Ngày tuyển dụng mới nhất</option>
          <option value="recruitment_date:asc">Ngày tuyển dụng cũ nhất</option>
        </Select>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data.items.length === 0 ? (
          <EmptyState
            title="Không tìm thấy nhân sự"
            description="Thử thay đổi từ khóa hoặc bộ lọc."
          />
        ) : (
          <>
            {isFetching && <div className="px-4 py-1 text-xs text-slate-400">Đang cập nhật...</div>}
            <Table columns={columns} rows={data.items} />
            <Pagination
              pagination={data.pagination}
              onChange={(page) => setFilters((f) => ({ ...f, page }))}
            />
          </>
        )}
      </div>

      <ConfirmDialog
        open={!!pendingDelete}
        onClose={() => setPendingDelete(null)}
        onConfirm={onDelete}
        loading={remove.isPending}
        title="Xác nhận xóa nhân sự"
        message={`Bạn có chắc muốn xóa nhân sự "${pendingDelete?.full_name}"? Thao tác là xóa mềm và có thể khôi phục sau.`}
        confirmText="Xóa"
      />
    </div>
  );
}
