const CONTACTS = [
  {
    icon: "📍",
    text: "Địa chỉ: 46 Phan Bội Châu, Phường Buôn Ma Thuột, Tỉnh Đắk Lắk",
  },
  { icon: "📞", text: "Số điện thoại: 012345789" },
  { icon: "✉️", text: "Email: admin@gmail.com" },
];

export default function Footer() {
  return (
    <footer className="border-t border-rule bg-paper px-4 py-6 text-ink-2 sm:px-6 md:px-8">
      <div className="mx-auto flex w-full max-w-[100rem] flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 lg:max-w-3xl">
          <span
            className="mb-3 block h-1 w-12 rounded-full"
            style={{ backgroundImage: "var(--gradient-brand-h)" }}
            aria-hidden="true"
          />
          <h2 className="font-display text-base font-semibold leading-snug text-ink sm:text-lg">
            VĂN PHÒNG ĐĂNG KÝ ĐẤT ĐAI TỈNH ĐẮK LẮK
          </h2>

          <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            {CONTACTS.map((row) => (
              <div key={row.text} className="flex items-start gap-2.5">
                <span
                  className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-[var(--color-accent-quiet)] text-xs"
                  aria-hidden="true"
                >
                  {row.icon}
                </span>
                <span className="min-w-0 break-words pt-1 leading-5">{row.text}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-rule bg-paper-2 px-4 py-3 text-sm lg:min-w-72">
          <div className="flex items-start gap-2.5">
            <span
              className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-[var(--color-accent-quiet)] text-xs"
              aria-hidden="true"
            >
              🕐
            </span>
            <div className="min-w-0 pt-0.5 leading-5">
              <p className="font-medium text-ink">Giờ làm việc: Thứ 2 – Thứ 6</p>
              <p className="mt-1 text-neutral">Sáng: 7:30 – 11:30</p>
              <p className="text-neutral">Chiều: 13:30 – 17:00</p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
