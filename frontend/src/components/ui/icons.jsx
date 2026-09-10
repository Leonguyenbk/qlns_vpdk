/* One icon set, one stroke voice. Lucide-style: 24x24, stroke 1.75, round caps,
 * currentColor. No emoji anywhere in the UI — these replace them. */
import clsx from "clsx";

function Icon({ children, size = 18, className, ...rest }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={clsx("shrink-0", className)}
      {...rest}
    >
      {children}
    </svg>
  );
}

export const IconOverview = (p) => (
  <Icon {...p}>
    <path d="M3 13h8V3H3zM13 21h8V3h-8zM3 21h8v-6H3z" />
  </Icon>
);
export const IconPeople = (p) => (
  <Icon {...p}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
  </Icon>
);
export const IconOrg = (p) => (
  <Icon {...p}>
    <rect x="4" y="3" width="16" height="7" rx="1.5" />
    <path d="M12 10v4M7 21v-4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v4" />
    <rect x="3" y="18" width="6" height="3" rx="1" />
    <rect x="15" y="18" width="6" height="3" rx="1" />
  </Icon>
);
export const IconPosition = (p) => (
  <Icon {...p}>
    <circle cx="12" cy="8" r="5" />
    <path d="m8.5 12.5-1.5 8L12 18l5 2.5-1.5-8" />
  </Icon>
);
export const IconKey = (p) => (
  <Icon {...p}>
    <circle cx="7.5" cy="15.5" r="4.5" />
    <path d="m10.7 12.3 8.3-8.3M16 6l3 3M14 8l3 3" />
  </Icon>
);
export const IconShield = (p) => (
  <Icon {...p}>
    <path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6z" />
    <path d="m9 12 2 2 4-4" />
  </Icon>
);
export const IconLog = (p) => (
  <Icon {...p}>
    <path d="M8 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-3" />
    <path d="M17 3h4v4M21 3l-9 9M8 8h4M8 12h3M8 16h6" />
  </Icon>
);
export const IconSearch = (p) => (
  <Icon {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-3.5-3.5" />
  </Icon>
);
export const IconMenu = (p) => (
  <Icon {...p}>
    <path d="M4 6h16M4 12h16M4 18h16" />
  </Icon>
);
export const IconClose = (p) => (
  <Icon {...p}>
    <path d="M6 6l12 12M18 6 6 18" />
  </Icon>
);
export const IconChevronLeft = (p) => (
  <Icon {...p}>
    <path d="m14 6-6 6 6 6" />
  </Icon>
);
export const IconChevronRight = (p) => (
  <Icon {...p}>
    <path d="m10 6 6 6-6 6" />
  </Icon>
);
export const IconChevronDown = (p) => (
  <Icon {...p}>
    <path d="m6 10 6 6 6-6" />
  </Icon>
);
export const IconLogout = (p) => (
  <Icon {...p}>
    <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3" />
    <path d="M10 17 5 12l5-5M5 12h11" />
  </Icon>
);
export const IconPlus = (p) => (
  <Icon {...p}>
    <path d="M12 5v14M5 12h14" />
  </Icon>
);
export const IconArrowRight = (p) => (
  <Icon {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Icon>
);
export const IconAlert = (p) => (
  <Icon {...p}>
    <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
    <path d="M12 9v4M12 17h.01" />
  </Icon>
);
export const IconInbox = (p) => (
  <Icon {...p}>
    <path d="M22 12h-6l-2 3h-4l-2-3H2" />
    <path d="M5.5 5.5 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.5A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.5Z" />
  </Icon>
);
export const IconRefresh = (p) => (
  <Icon {...p}>
    <path d="M21 12a9 9 0 1 1-3-6.7L21 8" />
    <path d="M21 3v5h-5" />
  </Icon>
);
export const IconUser = (p) => (
  <Icon {...p}>
    <circle cx="12" cy="8" r="3.5" />
    <path d="M5.5 20a6.5 6.5 0 0 1 13 0" />
  </Icon>
);
export const IconLock = (p) => (
  <Icon {...p}>
    <rect x="4.5" y="10.5" width="15" height="10" rx="2" />
    <path d="M8 10.5V7a4 4 0 0 1 8 0v3.5" />
  </Icon>
);
export const IconEye = (p) => (
  <Icon {...p}>
    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
    <circle cx="12" cy="12" r="3" />
  </Icon>
);
export const IconEyeOff = (p) => (
  <Icon {...p}>
    <path d="M3 3l18 18M10.6 10.6a3 3 0 0 0 4.2 4.2" />
    <path d="M9.9 5.2A9.5 9.5 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.4 4.3M6.6 6.6A17 17 0 0 0 2 12s3.5 7 10 7a9.6 9.6 0 0 0 4.1-.9" />
  </Icon>
);
