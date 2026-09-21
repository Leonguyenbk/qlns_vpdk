import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ErrorState, LoadingState } from "../components/ui/DataStates";
import NewsTabBar from "../components/NewsTabBar";
import { Modal } from "../components/ui/Modal";
import { Pagination } from "../components/ui/Table";
import {
  Badge,
  Button,
  FormField,
  PageHeader,
  Select,
  Textarea,
  TextInput,
} from "../components/ui/primitives";
import {
  IconClock,
  IconInbox,
  IconPeople,
  IconPlus,
  IconSend,
  IconTrash,
} from "../components/ui/icons";
import {
  useAnnouncementAudienceOptions,
  useAnnouncementMutations,
  useAnnouncements,
} from "../hooks/useAnnouncements";
import { apiErrorMessage } from "../lib/api";
import { PERMISSIONS } from "../lib/constants";
import { formatDateTime } from "../lib/format";

const EMPTY_FORM = {
  title: "",
  content: "",
  category: "Thông báo",
  audience_type: "ALL",
  audience_ids: [],
  is_pinned: false,
  expires_at: "",
};

const AUDIENCE_LABELS = {
  ALL: "Toàn Văn phòng",
  UNIT: "Theo đơn vị",
  ROLE: "Theo vai trò",
  USER: "Theo tài khoản",
};

const STATUS_LABELS = {
  draft: "Bản nháp",
  published: "Đang phát hành",
  archived: "Đã thu hồi",
};

const STATUS_BADGES = {
  draft: "badge-neutral",
  published: "badge-ok",
  archived: "badge-warn",
};

function toForm(item) {
  if (!item) return EMPTY_FORM;
  return {
    title: item.title || "",
    content: item.content || "",
    category: item.category || "Thông báo",
    audience_type: item.audience_type || "ALL",
    audience_ids: (item.audience_items || []).map((entry) => entry.id),
    is_pinned: Boolean(item.is_pinned),
    expires_at: item.expires_at ? new Date(item.expires_at).toISOString().slice(0, 16) : "",
  };
}

function AnnouncementEditor({ item, options, busy, onSave }) {
  const [form, setForm] = useState(() => toForm(item));
  const set = (patch) => setForm((current) => ({ ...current, ...patch }));
  const audienceOptions =
    form.audience_type === "UNIT"
      ? options?.units
      : form.audience_type === "ROLE"
        ? options?.roles
        : form.audience_type === "USER"
          ? options?.users
          : [];

  const submit = (event) => {
    event.preventDefault();
    if (!form.title.trim() || !form.content.trim()) {
      toast.error("Vui lòng nhập tiêu đề và nội dung thông báo.");
      return;
    }
    if (form.audience_type !== "ALL" && form.audience_ids.length === 0) {
      toast.error("Vui lòng chọn ít nhất một đối tượng nhận.");
      return;
    }
    onSave({
      ...form,
      title: form.title.trim(),
      content: form.content.trim(),
      category: form.category.trim() || "Thông báo",
      expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
    });
  };

  return (
    <form id="announcement-form" onSubmit={submit} className="space-y-1">
      <FormField label="Tiêu đề" required>
        <TextInput
          value={form.title}
          onChange={(event) => set({ title: event.target.value })}
          maxLength={255}
          autoFocus
        />
      </FormField>
      <FormField label="Loại thông báo">
        <TextInput
          value={form.category}
          onChange={(event) => set({ category: event.target.value })}
          placeholder="Thông báo, Lịch công tác, Văn bản mới…"
          maxLength={50}
        />
      </FormField>
      <FormField label="Nội dung" required>
        <Textarea
          value={form.content}
          onChange={(event) => set({ content: event.target.value })}
          rows={7}
        />
      </FormField>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Đối tượng nhận">
          <Select
            value={form.audience_type}
            onChange={(event) =>
              set({ audience_type: event.target.value, audience_ids: [] })
            }
          >
            {Object.entries(AUDIENCE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </FormField>
        <FormField label="Hết hiệu lực" hint="Để trống nếu không giới hạn thời gian">
          <TextInput
            type="datetime-local"
            value={form.expires_at}
            onChange={(event) => set({ expires_at: event.target.value })}
          />
        </FormField>
      </div>
      {form.audience_type !== "ALL" && (
        <FormField
          label="Danh sách người nhận"
          hint="Giữ Ctrl để chọn nhiều mục trên máy tính"
          required
        >
          <select
            multiple
            size={6}
            className="input h-auto py-2"
            value={form.audience_ids.map(String)}
            onChange={(event) =>
              set({
                audience_ids: Array.from(event.target.selectedOptions, (option) =>
                  Number(option.value),
                ),
              })
            }
          >
            {(audienceOptions || []).map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
                {option.username ? ` (${option.username})` : ""}
              </option>
            ))}
          </select>
        </FormField>
      )}
      <label className="flex items-center gap-2 pb-2 text-sm text-ink-2">
        <input
          type="checkbox"
          checked={form.is_pinned}
          onChange={(event) => set({ is_pinned: event.target.checked })}
          className="h-4 w-4 rounded border-rule-2 accent-[var(--color-accent)]"
        />
        Ghim thông báo lên đầu bảng tin
      </label>
      <div className="sr-only" aria-live="polite">
        {busy ? "Đang lưu" : ""}
      </div>
    </form>
  );
}

function AnnouncementCard({ item, canCreate, canPublish, canManage, userId, actions }) {
  const canEdit = canManage || (canCreate && item.created_by === userId);
  const audience = item.audience_items?.length
    ? item.audience_items.map((entry) => entry.name).join(", ")
    : AUDIENCE_LABELS[item.audience_type];

  return (
    <article
      className={`card overflow-hidden p-0 ${
        !item.is_read && item.status === "published" ? "ring-1 ring-[var(--color-focus)]" : ""
      }`}
    >
      <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-start">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[var(--color-accent-quiet)] text-accent-text">
          <IconInbox size={21} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            {item.is_pinned && <Badge className="badge-info">Đã ghim</Badge>}
            {item.status !== "published" && (
              <Badge className={STATUS_BADGES[item.status]}>{STATUS_LABELS[item.status]}</Badge>
            )}
            {!item.is_read && item.status === "published" && (
              <Badge className="badge-info">Chưa đọc</Badge>
            )}
            <span className="text-xs font-medium uppercase tracking-wide text-accent-text">
              {item.category}
            </span>
          </div>
          <h2 className="mt-2 font-display text-lg font-semibold text-ink">{item.title}</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink-2">{item.content}</p>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted">
            <span className="inline-flex items-center gap-1.5">
              <IconClock size={14} />
              {formatDateTime(item.published_at || item.created_at)}
            </span>
            <span className="inline-flex min-w-0 items-center gap-1.5">
              <IconPeople size={14} />
              <span className="truncate">{audience}</span>
            </span>
            {item.creator_name && <span>Người soạn: {item.creator_name}</span>}
            {item.expires_at && <span>Hết hiệu lực: {formatDateTime(item.expires_at)}</span>}
          </div>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-end gap-2 border-t border-rule bg-paper-2 px-5 py-3">
        {!item.is_read && item.status === "published" && (
          <Button variant="ghost" onClick={() => actions.markRead(item.id)}>
            Đánh dấu đã đọc
          </Button>
        )}
        {canEdit && (
          <Button variant="secondary" onClick={() => actions.edit(item)}>
            Chỉnh sửa
          </Button>
        )}
        {canPublish && item.status !== "published" && (
          <Button onClick={() => actions.status(item.id, "published")}>
            <IconSend size={15} /> Phát hành
          </Button>
        )}
        {canPublish && item.status === "published" && (
          <Button variant="secondary" onClick={() => actions.status(item.id, "archived")}>
            Thu hồi
          </Button>
        )}
        {canEdit && item.status !== "published" && (
          <Button variant="ghost" className="text-danger" onClick={() => actions.remove(item)}>
            <IconTrash size={15} /> Xóa
          </Button>
        )}
      </div>
    </article>
  );
}

export default function OverviewPage() {
  const { user, hasPermission } = useAuth();
  const canCreate = hasPermission(PERMISSIONS.ANNOUNCEMENT_CREATE);
  const canPublish =
    hasPermission(PERMISSIONS.ANNOUNCEMENT_PUBLISH) ||
    hasPermission(PERMISSIONS.ANNOUNCEMENT_MANAGE);
  const canManage = hasPermission(PERMISSIONS.ANNOUNCEMENT_MANAGE);
  const canEditAny = canCreate || canManage;
  const includeAll = canEditAny || canPublish;
  const [page, setPage] = useState(1);
  const params = useMemo(
    () => ({ include_all: includeAll ? 1 : undefined, page }),
    [includeAll, page],
  );
  const { data, isLoading, isError, error, refetch } = useAnnouncements(params);
  const { data: options } = useAnnouncementAudienceOptions(canEditAny);
  const mutations = useAnnouncementMutations();
  const [editing, setEditing] = useState(null);
  const [editorOpen, setEditorOpen] = useState(false);

  const save = async (body) => {
    try {
      if (editing) await mutations.update.mutateAsync({ id: editing.id, body });
      else await mutations.create.mutateAsync(body);
      toast.success(editing ? "Đã cập nhật thông báo" : "Đã lưu bản nháp thông báo");
      setEditorOpen(false);
      setEditing(null);
    } catch (saveError) {
      toast.error(apiErrorMessage(saveError));
    }
  };

  const actions = {
    edit: (item) => {
      setEditing(item);
      setEditorOpen(true);
    },
    markRead: async (id) => {
      try {
        await mutations.markRead.mutateAsync(id);
      } catch (markError) {
        toast.error(apiErrorMessage(markError));
      }
    },
    status: async (id, status) => {
      try {
        await mutations.setStatus.mutateAsync({ id, status });
        toast.success(status === "published" ? "Đã phát hành thông báo" : "Đã thu hồi thông báo");
      } catch (statusError) {
        toast.error(apiErrorMessage(statusError));
      }
    },
    remove: async (item) => {
      if (!window.confirm(`Xóa thông báo “${item.title}”?`)) return;
      try {
        await mutations.remove.mutateAsync(item.id);
        toast.success("Đã xóa thông báo");
      } catch (removeError) {
        toast.error(apiErrorMessage(removeError));
      }
    },
  };

  return (
    <div>
      <PageHeader
        eyebrow="Văn phòng Đăng ký Đất đai"
        title="Tổng quan"
        subtitle="Thông báo, lịch công tác và văn bản mới dành cho bạn"
        actions={
          canEditAny && (
            <Button
              onClick={() => {
                setEditing(null);
                setEditorOpen(true);
              }}
            >
              <IconPlus size={15} /> Soạn thông báo
            </Button>
          )
        }
      />

      <NewsTabBar />

      {data?.unread > 0 && (
        <div className="mb-5 rounded-xl border border-[var(--color-focus)] bg-[var(--color-accent-quiet)] px-4 py-3 text-sm text-accent-text">
          Bạn có {data.unread} thông báo chưa đọc trên trang này.
        </div>
      )}

      {isLoading ? (
        <LoadingState label="Đang tải bảng tin…" />
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : !data?.items?.length ? (
        <div className="card">
          <EmptyState
            title="Chưa có thông báo"
            description="Các thông báo của Văn phòng sẽ xuất hiện tại đây."
            action={
              canEditAny && (
                <Button onClick={() => setEditorOpen(true)}>
                  <IconPlus size={15} /> Soạn thông báo đầu tiên
                </Button>
              )
            }
          />
        </div>
      ) : (
        <div className="space-y-4">
          {data.items.map((item) => (
            <AnnouncementCard
              key={item.id}
              item={item}
              canCreate={canCreate}
              canPublish={canPublish}
              canManage={canManage}
              userId={user?.id}
              actions={actions}
            />
          ))}
          <div className="card overflow-hidden p-0">
            <Pagination pagination={data.pagination} onChange={setPage} />
          </div>
        </div>
      )}

      <Modal
        open={editorOpen}
        onClose={() => {
          setEditorOpen(false);
          setEditing(null);
        }}
        title={editing ? "Chỉnh sửa thông báo" : "Soạn thông báo"}
        size="lg"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => {
                setEditorOpen(false);
                setEditing(null);
              }}
            >
              Hủy
            </Button>
            <Button
              type="submit"
              form="announcement-form"
              disabled={mutations.create.isPending || mutations.update.isPending}
            >
              {mutations.create.isPending || mutations.update.isPending ? "Đang lưu…" : "Lưu bản nháp"}
            </Button>
          </>
        }
      >
        <AnnouncementEditor
          key={editing?.id || "new"}
          item={editing}
          options={options}
          busy={mutations.create.isPending || mutations.update.isPending}
          onSave={save}
        />
      </Modal>
    </div>
  );
}
