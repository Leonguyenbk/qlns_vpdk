import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useUnits } from "../../hooks/useUnits";
import { useCatalogGroups, useProducts } from "../../hooks/useKpi";
import { useAssignablePeople, useTaskMutations, useWorkload } from "../../hooks/useTasks";
import { apiErrorMessage } from "../../lib/api";
import { todayISO } from "../../lib/format";
import { TASK_SOURCE_LABELS, TASK_PRIORITY_LABELS, TASK_DEADLINE_TYPE_LABELS } from "../../lib/constants";
import { PageHeader, Button, FormField, TextInput, Select, Textarea } from "../../components/ui/primitives";

function WorkloadHint({ userId }) {
  const { data } = useWorkload(userId);
  if (!data) return null;
  return (
    <p className="mt-1 text-xs text-muted">
      Đang phụ trách {data.active_task_count} nhiệm vụ ({data.overdue_count} quá hạn), tổng khối lượng giao{" "}
      {data.total_assigned_workload}. {data.basis}
    </p>
  );
}

export default function TaskCreatePage() {
  const navigate = useNavigate();
  const { data: units } = useUnits({ only_active: true });
  const { data: groups } = useCatalogGroups();
  const [assignSearch, setAssignSearch] = useState("");
  const { data: candidates } = useAssignablePeople({ search: assignSearch });
  const { create } = useTaskMutations();

  const [form, setForm] = useState({
    name: "", description: "", assigning_unit_id: "", source: "AD_HOC", priority: "NORMAL",
    deadline_type: "INTERNAL", assigned_date: todayISO(), original_deadline: "",
    assigned_workload: "", workload_unit: "", business_group_code: "", product_id: "",
    output_description: "", quality_standard: "", acceptance_conditions: "",
  });
  const [assignees, setAssignees] = useState([{ user_id: "", role_in_task: "LEAD", contribution_percent: "" }]);
  const set = (patch) => setForm((f) => ({ ...f, ...patch }));

  const { data: products } = useProducts(form.business_group_code ? { group_code: form.business_group_code } : {});

  const updateAssignee = (idx, patch) =>
    setAssignees((list) => list.map((a, i) => (i === idx ? { ...a, ...patch } : a)));
  const addAssigneeRow = () =>
    setAssignees((list) => [...list, { user_id: "", role_in_task: "COLLABORATOR", contribution_percent: "" }]);
  const removeAssigneeRow = (idx) => setAssignees((list) => list.filter((_, i) => i !== idx));

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return toast.error("Tên nhiệm vụ là bắt buộc.");
    if (!form.assigning_unit_id) return toast.error("Chọn đơn vị giao việc.");
    const validAssignees = assignees.filter((a) => a.user_id);
    if (validAssignees.length === 0) return toast.error("Chọn ít nhất một người thực hiện.");

    try {
      const body = {
        ...form,
        assigning_unit_id: Number(form.assigning_unit_id),
        product_id: form.product_id ? Number(form.product_id) : null,
        assigned_workload: form.assigned_workload ? Number(form.assigned_workload) : null,
        original_deadline: form.original_deadline || null,
        assignees: validAssignees.map((a) => ({
          user_id: Number(a.user_id), role_in_task: a.role_in_task,
          contribution_percent: a.contribution_percent ? Number(a.contribution_percent) : null,
        })),
      };
      const resp = await create.mutateAsync(body);
      toast.success("Tạo và giao nhiệm vụ thành công");
      navigate(`/giao-viec/${resp.data.data.id}`);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <div>
      <PageHeader title="Giao việc mới" subtitle="Ghi nhận đầy đủ nhiệm vụ, người thực hiện và tiêu chí nghiệm thu." />
      <form onSubmit={onSubmit} className="card space-y-5 p-5">
        <FormField label="Tên nhiệm vụ" required>
          <TextInput value={form.name} onChange={(e) => set({ name: e.target.value })} />
        </FormField>
        <FormField label="Mô tả">
          <Textarea value={form.description} onChange={(e) => set({ description: e.target.value })} />
        </FormField>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <FormField label="Đơn vị giao việc" required>
            <Select value={form.assigning_unit_id} onChange={(e) => set({ assigning_unit_id: e.target.value })}>
              <option value="">— Chọn đơn vị —</option>
              {units?.map((u) => <option key={u.id} value={u.id}>{u.path || u.name}</option>)}
            </Select>
          </FormField>
          <FormField label="Nguồn nhiệm vụ">
            <Select value={form.source} onChange={(e) => set({ source: e.target.value })}>
              {Object.entries(TASK_SOURCE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </Select>
          </FormField>
          <FormField label="Mức ưu tiên">
            <Select value={form.priority} onChange={(e) => set({ priority: e.target.value })}>
              {Object.entries(TASK_PRIORITY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </Select>
          </FormField>
          <FormField label="Ngày giao">
            <TextInput type="date" value={form.assigned_date} onChange={(e) => set({ assigned_date: e.target.value })} />
          </FormField>
          <FormField label="Hạn hoàn thành">
            <TextInput type="date" value={form.original_deadline} onChange={(e) => set({ original_deadline: e.target.value })} />
          </FormField>
          <FormField label="Loại hạn">
            <Select value={form.deadline_type} onChange={(e) => set({ deadline_type: e.target.value })}>
              {Object.entries(TASK_DEADLINE_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </Select>
          </FormField>
          <FormField label="Nhóm nghiệp vụ (danh mục 18 nhóm)">
            <Select value={form.business_group_code} onChange={(e) => set({ business_group_code: e.target.value, product_id: "" })}>
              <option value="">— Không phân loại —</option>
              {groups?.map((g) => <option key={g.code} value={g.code}>{g.code} — {g.name}</option>)}
            </Select>
          </FormField>
          <FormField label="Sản phẩm chuẩn (nếu có, dùng để quy đổi KPI)">
            <Select value={form.product_id} onChange={(e) => set({ product_id: e.target.value })}>
              <option value="">— Chưa gắn sản phẩm chuẩn —</option>
              {products?.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}
            </Select>
          </FormField>
          <FormField label="Khối lượng giao" hint="Số lượng sản phẩm/công việc — dùng làm mẫu số/tử số khi tính KPI theo kỳ.">
            <TextInput type="number" step="0.01" value={form.assigned_workload} onChange={(e) => set({ assigned_workload: e.target.value })} />
          </FormField>
          <FormField label="Đơn vị tính">
            <TextInput placeholder="hồ sơ, văn bản, thửa đất…" value={form.workload_unit} onChange={(e) => set({ workload_unit: e.target.value })} />
          </FormField>
        </div>

        <FormField label="Yêu cầu đầu ra / tiêu chuẩn chất lượng">
          <Textarea value={form.output_description} onChange={(e) => set({ output_description: e.target.value })} />
        </FormField>
        <FormField label="Điều kiện nghiệm thu">
          <Textarea value={form.acceptance_conditions} onChange={(e) => set({ acceptance_conditions: e.target.value })} />
        </FormField>

        <div className="border-t border-rule pt-4">
          <h3 className="mb-2 text-sm font-semibold text-ink">Người thực hiện</h3>
          <TextInput
            className="mb-3 max-w-sm" placeholder="Tìm người theo tên…"
            value={assignSearch} onChange={(e) => setAssignSearch(e.target.value)}
          />
          <div className="space-y-2">
            {assignees.map((a, idx) => (
              <div key={idx} className="grid gap-2 sm:grid-cols-4">
                <Select value={a.user_id} onChange={(e) => updateAssignee(idx, { user_id: e.target.value })}>
                  <option value="">— Chọn người —</option>
                  {candidates?.map((c) => (
                    <option key={c.user_id} value={c.user_id}>
                      {c.full_name} — {c.unit_name || "?"} ({c.position_name || "?"})
                    </option>
                  ))}
                </Select>
                <Select value={a.role_in_task} onChange={(e) => updateAssignee(idx, { role_in_task: e.target.value })}>
                  <option value="LEAD">Chủ trì</option>
                  <option value="COLLABORATOR">Phối hợp</option>
                </Select>
                <TextInput
                  type="number" placeholder="% đóng góp (nếu nhiều người cùng 1 sản phẩm)"
                  value={a.contribution_percent} onChange={(e) => updateAssignee(idx, { contribution_percent: e.target.value })}
                />
                <div className="flex items-center gap-2">
                  {a.user_id && <WorkloadHint userId={Number(a.user_id)} />}
                  {assignees.length > 1 && (
                    <Button variant="ghost" className="px-2 py-1 text-xs text-danger" onClick={() => removeAssigneeRow(idx)}>
                      Bỏ
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
          <Button type="button" variant="secondary" className="mt-2" onClick={addAssigneeRow}>
            + Thêm người cùng làm
          </Button>
          <p className="mt-2 text-xs text-muted">
            Nếu nhiều người cùng làm chung một sản phẩm, nhập % đóng góp — tổng phải bằng 100%.
            Nếu mỗi người làm sản phẩm riêng của mình, hãy tạo nhiệm vụ riêng cho từng người thay vì gộp chung.
          </p>
        </div>

        <div className="flex justify-end gap-2 border-t border-rule pt-4">
          <Button type="button" variant="secondary" onClick={() => navigate(-1)}>Hủy</Button>
          <Button type="submit" disabled={create.isPending}>Giao việc</Button>
        </div>
      </form>
    </div>
  );
}
