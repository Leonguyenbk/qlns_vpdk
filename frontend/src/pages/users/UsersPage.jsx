import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useUsers, useUserMutations } from "../../hooks/useUsers";
import { useRoles } from "../../hooks/useRoles";
import { useUnits } from "../../hooks/useUnits";
import { useCan } from "../../components/Can";
import { PERMISSIONS } from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import { PageHeader, Button, Badge, Card, FormField, Select, TextInput, PasswordInput } from "../../components/ui/primitives";
import { Table, Pagination } from "../../components/ui/Table";
import { LoadingState, ErrorState, EmptyState } from "../../components/ui/DataStates";
import { Modal } from "../../components/ui/Modal";
import { EmployeePicker } from "../../components/employees/EmployeePicker";

function UserEditor({ user, roles, units, onClose }) {
  const { update, setRoles, setScopes, resetPassword } = useUserMutations();
  const [roleIds, setRoleIds] = useState(user.roles.map((r) => r.id));
  const [active, setActive] = useState(user.is_active);
  const [employeeId, setEmployeeId] = useState(user.employee_id);
  const [scopes, setScopeList] = useState(
    user.unit_scopes.map((s) => ({ scope_type: s.scope_type, unit_id: s.unit_id || "" }))
  );

  const save = async () => {
    try {
      await update.mutateAsync({ id: user.id, body: { is_active: active, employee_id: employeeId } });
      await setRoles.mutateAsync({ id: user.id, role_ids: roleIds });
      await setScopes.mutateAsync({
        id: user.id,
        scopes: scopes.map((s) => ({
          scope_type: s.scope_type,
          unit_id: s.scope_type === "GLOBAL" ? null : Number(s.unit_id),
        })),
      });
      toast.success("Đã lưu tài khoản");
      onClose();
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const doReset = async () => {
    try {
      const res = await resetPassword.mutateAsync({ id: user.id, body: {} });
      const pwd = res.data.data?.new_password;
      toast.success(pwd ? `Mật khẩu mới: ${pwd}` : "Đã đặt lại mật khẩu", { duration: 8000 });
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title={`Tài khoản: ${user.username}`}
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Hủy
          </Button>
          <Button onClick={save} disabled={update.isPending}>
            Lưu
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} /> Tài
          khoản đang hoạt động
        </label>

        <FormField
          label="Liên kết hồ sơ nhân sự"
          hint="Độc lập hoặc liên kết đều được — chọn để tài khoản thấy đúng &quot;Công việc của tôi&quot;/&quot;KPI của tôi&quot; theo hồ sơ nhân sự"
        >
          <EmployeePicker value={employeeId} onChange={(id) => setEmployeeId(id)} />
        </FormField>

        <div>
          <p className="label">Vai trò</p>
          <div className="flex flex-wrap gap-2">
            {roles?.map((r) => {
              const checked = roleIds.includes(r.id);
              return (
                <button
                  key={r.id}
                  type="button"
                  onClick={() =>
                    setRoleIds((ids) =>
                      checked ? ids.filter((x) => x !== r.id) : [...ids, r.id]
                    )
                  }
                  className={`badge ${
                    checked ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {r.name}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <p className="label">Phạm vi đơn vị</p>
          <div className="space-y-2">
            {scopes.map((s, idx) => (
              <div key={idx} className="flex gap-2">
                <Select
                  value={s.scope_type}
                  onChange={(e) =>
                    setScopeList((list) =>
                      list.map((x, i) => (i === idx ? { ...x, scope_type: e.target.value } : x))
                    )
                  }
                >
                  <option value="GLOBAL">Toàn hệ thống</option>
                  <option value="UNIT">Một đơn vị</option>
                  <option value="SUBTREE">Đơn vị + cấp dưới</option>
                </Select>
                {s.scope_type !== "GLOBAL" && (
                  <Select
                    value={s.unit_id}
                    onChange={(e) =>
                      setScopeList((list) =>
                        list.map((x, i) => (i === idx ? { ...x, unit_id: e.target.value } : x))
                      )
                    }
                  >
                    <option value="">-- Đơn vị --</option>
                    {units?.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.code} – {u.name}
                      </option>
                    ))}
                  </Select>
                )}
                <Button
                  variant="ghost"
                  className="text-red-600"
                  onClick={() => setScopeList((list) => list.filter((_, i) => i !== idx))}
                >
                  ✕
                </Button>
              </div>
            ))}
            <Button
              variant="secondary"
              className="text-xs"
              onClick={() => setScopeList((list) => [...list, { scope_type: "UNIT", unit_id: "" }])}
            >
              + Thêm phạm vi
            </Button>
          </div>
        </div>

        <div className="border-t border-slate-200 pt-3">
          <Button variant="secondary" onClick={doReset} disabled={resetPassword.isPending}>
            Đặt lại mật khẩu (sinh ngẫu nhiên)
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function CreateUser({ roles, onClose }) {
  const { create } = useUserMutations();
  // Mặc định chọn sẵn "Viên chức (tự phục vụ)" — mọi tài khoản nên có ít nhất
  // vai trò này để tự xem được nhiệm vụ/KPI của mình dù không được phân thêm
  // quyền gì khác; backend cũng tự gán vai trò này nếu để trống hoàn toàn.
  const [form, setForm] = useState(() => {
    const staff = roles?.find((r) => r.code === "STAFF");
    return {
      username: "",
      full_name: "",
      email: "",
      password: "",
      employee_id: null,
      role_ids: staff ? [staff.id] : [],
    };
  });

  const onPickEmployee = (employeeId, employee) => {
    setForm((f) => ({
      ...f,
      employee_id: employeeId,
      // Chỉ tự điền họ tên nếu admin chưa gõ gì — không ghi đè nếu đã nhập tay.
      full_name: !f.full_name && employee ? employee.full_name : f.full_name,
    }));
  };

  const submit = async () => {
    try {
      await create.mutateAsync({ ...form });
      toast.success("Tạo tài khoản thành công");
      onClose();
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      title="Thêm tài khoản"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Hủy
          </Button>
          <Button onClick={submit} disabled={create.isPending}>
            Tạo
          </Button>
        </>
      }
    >
      <div className="grid gap-3">
        <FormField
          label="Liên kết hồ sơ nhân sự"
          hint="Chọn để tài khoản tự thấy &quot;Công việc của tôi&quot;/&quot;KPI của tôi&quot; theo đúng hồ sơ — bỏ trống nếu là tài khoản không gắn nhân sự (vd. tài khoản dùng chung)"
        >
          <EmployeePicker value={form.employee_id} onChange={onPickEmployee} />
        </FormField>
        <FormField label="Tên đăng nhập" required>
          <TextInput value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
        </FormField>
        <FormField label="Họ tên" required>
          <TextInput value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        </FormField>
        <FormField label="Email">
          <TextInput value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </FormField>
        <FormField label="Mật khẩu" required hint="Tối thiểu 8 ký tự">
          <PasswordInput
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </FormField>
        <div>
          <p className="label">Vai trò</p>
          <div className="flex flex-wrap gap-2">
            {roles?.map((r) => {
              const checked = form.role_ids.includes(r.id);
              return (
                <button
                  key={r.id}
                  type="button"
                  className={`badge ${checked ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"}`}
                  onClick={() =>
                    setForm((f) => ({
                      ...f,
                      role_ids: checked
                        ? f.role_ids.filter((x) => x !== r.id)
                        : [...f.role_ids, r.id],
                    }))
                  }
                >
                  {r.name}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </Modal>
  );
}

const DEFAULT_FILTERS = {
  keyword: "",
  role_id: "",
  unit_id: "",
  is_active: "",
  page: 1,
  page_size: 10,
};

export default function UsersPage() {
  const { can } = useCan();
  const canManage = can(PERMISSIONS.USER_MANAGE);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const setFilter = (patch) => setFilters((f) => ({ ...f, ...patch, page: 1 }));

  const params = useMemo(() => {
    const p = { ...filters };
    Object.keys(p).forEach((k) => p[k] === "" && delete p[k]);
    return p;
  }, [filters]);

  const { data, isLoading, isError, error, refetch } = useUsers(params);
  const { data: roles } = useRoles();
  const { data: units } = useUnits();
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);

  const columns = [
    { key: "username", header: "Tên đăng nhập", render: (r) => <span className="font-medium">{r.username}</span> },
    { key: "full_name", header: "Họ tên" },
    { key: "email", header: "Email", render: (r) => r.email || "—" },
    {
      key: "roles",
      header: "Vai trò",
      render: (r) => (
        <div className="flex flex-wrap gap-1">
          {r.roles.map((role) => (
            <Badge key={role.id}>{role.name}</Badge>
          ))}
        </div>
      ),
    },
    {
      key: "is_active",
      header: "Trạng thái",
      render: (r) =>
        r.is_active ? (
          <Badge className="bg-green-100 text-green-700">Hoạt động</Badge>
        ) : (
          <Badge className="bg-red-100 text-red-700">Khóa</Badge>
        ),
    },
    { key: "last_login_at", header: "Đăng nhập gần nhất", render: (r) => formatDateTime(r.last_login_at) },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (r) =>
        canManage && (
          <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => setEditing(r)}>
            Phân quyền
          </Button>
        ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Quản lý tài khoản"
        actions={canManage && <Button onClick={() => setCreating(true)}>+ Thêm tài khoản</Button>}
      />
      <div className="card mb-4 grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-4">
        <TextInput
          placeholder="Tìm theo tên đăng nhập, họ tên, email..."
          value={filters.keyword}
          onChange={(e) => setFilter({ keyword: e.target.value })}
        />
        <Select value={filters.role_id} onChange={(e) => setFilter({ role_id: e.target.value })}>
          <option value="">Tất cả vai trò</option>
          {roles?.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </Select>
        <Select value={filters.unit_id} onChange={(e) => setFilter({ unit_id: e.target.value })}>
          <option value="">Tất cả đơn vị</option>
          {units?.map((u) => (
            <option key={u.id} value={u.id}>
              {u.path || u.name}
            </option>
          ))}
        </Select>
        <Select value={filters.is_active} onChange={(e) => setFilter({ is_active: e.target.value })}>
          <option value="">Tất cả trạng thái</option>
          <option value="true">Hoạt động</option>
          <option value="false">Khóa</option>
        </Select>
      </div>

      <Card className="overflow-hidden p-0">
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data.items.length === 0 ? (
          <EmptyState title="Không tìm thấy tài khoản phù hợp" />
        ) : (
          <>
            <Table columns={columns} rows={data.items} />
            <Pagination pagination={data.pagination} onChange={(page) => setFilters((f) => ({ ...f, page }))} />
          </>
        )}
      </Card>

      {editing && (
        <UserEditor user={editing} roles={roles} units={units} onClose={() => setEditing(null)} />
      )}
      {creating && <CreateUser roles={roles} onClose={() => setCreating(false)} />}
    </div>
  );
}
