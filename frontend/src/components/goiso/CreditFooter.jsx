/* Dòng ghi công cố định ở chân màn hình công khai — port từ _credit.html. */
const DEFAULT_CREDIT =
  "Phòng Dữ liệu - Thông tin đất đai\nTổ Ứng dụng và Phát triển công nghệ";

export function CreditFooter({ text }) {
  const lines = (text || DEFAULT_CREDIT).split("\n");
  return (
    <div
      className="pointer-events-none fixed inset-x-0 bottom-0 border-t border-[#dbe4ee] bg-white/92 px-2.5 py-1.5 text-center text-[15px] font-semibold leading-tight text-brand-600"
      style={{ zIndex: 60 }}
    >
      {lines.map((l, i) => (
        <span key={i}>
          {l}
          {i < lines.length - 1 && <br />}
        </span>
      ))}
    </div>
  );
}
