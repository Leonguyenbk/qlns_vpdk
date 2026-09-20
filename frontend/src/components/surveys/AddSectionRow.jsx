import { useState } from "react";
import toast from "react-hot-toast";
import { apiErrorMessage } from "../../lib/api";
import { Button, TextInput } from "../ui/primitives";

/** Ô tạo phần mới ngay trong danh sách — phần vừa tạo hiện thành khối riêng để thêm câu hỏi. */
export function AddSectionRow({ mutations }) {
  const [title, setTitle] = useState("");

  const create = async () => {
    const value = title.trim();
    if (!value) return;
    try {
      await mutations.create.mutateAsync({ title: value });
      setTitle("");
      toast.success("Đã tạo phần — thêm câu hỏi ngay trong phần đó");
    } catch (error) {
      toast.error(apiErrorMessage(error));
    }
  };

  return (
    <div className="flex gap-2 rounded-xl border border-dashed border-rule p-3">
      <TextInput
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        onKeyDown={(event) => event.key === "Enter" && create()}
        placeholder="Tên phần mới, ví dụ: Phần 1. Tiếp cận dịch vụ"
        aria-label="Tên phần mới"
      />
      <Button variant="secondary" className="shrink-0" onClick={create} disabled={mutations.create.isPending}>
        + Thêm phần
      </Button>
    </div>
  );
}
