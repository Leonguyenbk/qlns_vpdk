import { useEffect, useRef } from "react";
import { API_BASE_URL } from "./constants";

const API_ROOT = API_BASE_URL.replace(/\/api\/?$/, "");

/* Kết nối SSE /api/b/<code>/stream, tự nối lại khi rớt (giống common.js gốc).
 * onEvent nhận {type:'snapshot',...} | {type:'call',...} | {type:'_disconnected'}. */
export function useGoisoStream(branchCode, onEvent) {
  const cbRef = useRef(onEvent);
  cbRef.current = onEvent;

  useEffect(() => {
    if (!branchCode) return undefined;
    let es = null;
    let retry = 0;
    let stopped = false;
    let timer = null;

    function open() {
      if (stopped) return;
      es = new EventSource(`${API_ROOT}/api/b/${encodeURIComponent(branchCode)}/stream`);
      es.onopen = () => {
        retry = 0;
      };
      es.onmessage = (e) => {
        if (!e.data) return;
        try {
          cbRef.current(JSON.parse(e.data));
        } catch {
          /* ignore malformed frame */
        }
      };
      es.onerror = () => {
        es.close();
        if (stopped) return;
        retry = Math.min(retry + 1, 6);
        timer = setTimeout(open, 1000 * retry);
        cbRef.current({ type: "_disconnected" });
      };
    }
    open();

    return () => {
      stopped = true;
      clearTimeout(timer);
      es?.close();
    };
  }, [branchCode]);
}
