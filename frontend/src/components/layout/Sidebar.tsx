import { NavLink } from "react-router-dom";

function IconChart() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="shrink-0">
      <rect x="1" y="8" width="3" height="6" rx="0.5" fill="currentColor" opacity="0.5" />
      <rect x="6" y="4" width="3" height="10" rx="0.5" fill="currentColor" opacity="0.75" />
      <rect x="11" y="1" width="3" height="13" rx="0.5" fill="currentColor" />
    </svg>
  );
}

function IconGantt() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="shrink-0">
      <rect x="1" y="2" width="8" height="2.5" rx="0.5" fill="currentColor" />
      <rect x="4" y="6.25" width="9" height="2.5" rx="0.5" fill="currentColor" opacity="0.75" />
      <rect x="1" y="10.5" width="6" height="2.5" rx="0.5" fill="currentColor" opacity="0.5" />
    </svg>
  );
}

function IconChain() {
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none" className="shrink-0">
      <path
        d="M5.5 8.5L9.5 4.5M6.5 3.5L8 2a2.828 2.828 0 114 4L10.5 7.5M4.5 8.5L3 10a2.828 2.828 0 104 4L8.5 12.5"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

const links = [
  { to: "/", label: "Dashboard", Icon: IconChart },
  { to: "/schedule", label: "Schedule", Icon: IconGantt },
  { to: "/certificates", label: "Audit Log", Icon: IconChain },
];

export default function Sidebar() {
  return (
    <nav className="w-48 bg-gray-950 border-r border-gray-800/60 flex flex-col py-5 px-2.5 shrink-0">
      <div className="mb-7 px-2">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />
          <span className="text-sm font-semibold tracking-tight text-white">gridshift</span>
        </div>
        <p className="text-[10px] text-gray-600 mt-1 ml-3.5 font-mono">YKH · TEPCO-KT</p>
      </div>

      <ul className="space-y-0.5 flex-1">
        {links.map(({ to, label, Icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-2.5 py-2 rounded text-xs transition-colors ${
                  isActive
                    ? "bg-gray-800 text-gray-100"
                    : "text-gray-500 hover:text-gray-300 hover:bg-gray-900"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span className={isActive ? "text-emerald-400" : ""}>
                    <Icon />
                  </span>
                  {label}
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>

      <div className="px-2.5 pt-4 border-t border-gray-800/60">
        <p className="text-[10px] text-gray-700 font-mono leading-relaxed">
          LP solver · HiGHS<br />
          Open-Meteo · JEPX
        </p>
      </div>
    </nav>
  );
}
