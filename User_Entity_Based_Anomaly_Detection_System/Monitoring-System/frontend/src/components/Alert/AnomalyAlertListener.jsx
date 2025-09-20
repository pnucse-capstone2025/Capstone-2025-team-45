// components/AnomalyAlertListener.jsx
import React, { useEffect, useRef, useState } from 'react';
import { Snackbar, Alert } from '@mui/material';

const API_URL =process.env.REACT_APP_API_URL

const WS_BASE = API_URL.replace(/^http/, 'ws').replace(/\/+$/, '');

export default function AnomalyAlertListener({ organizationid }) {
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const mountedRef = useRef(false);
  const backoffRef = useRef(1000); // 재연결 backoff (최대 30s)
  const manualCloseRef = useRef(false);

  const [open, setOpen] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!organizationid) return;
    mountedRef.current = true;
    manualCloseRef.current = false;

    const url = `${WS_BASE}/ws/alerts/${organizationid}`;
    console.log('WS connect:', url);

    const connect = () => {
      // 이미 열려있거나 연결 중이면 또 만들지 않기
      if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
        return;
      }
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WS open');
        backoffRef.current = 1000; // 성공하면 backoff 초기화
      };

      ws.onmessage = (evt) => {
        let data = evt.data;
        if (typeof data === 'string') {
          try { data = JSON.parse(data); } catch {}
        }
        console.log('WS msg:', data);
        const t = String(data?.type || '');
        if (t === 'anomaly_user_logon' || t === 'anomaly_logon' || t === 'hello') {
          setMsg(data.message || `알림: 악성 사용자 로그온이 감지되어, 자동으로 차단되었습니다. ${JSON.stringify(data)}`);
          setOpen(true);
        }
      };

      ws.onerror = (e) => {
        console.error('WS error', e);
        // 에러는 곧 close로 이어질 수 있으니 여기서 직접 재연결 예약은 하지 않음
      };

      ws.onclose = (e) => {
        console.log('WS close', e.code, e.reason || '');
        wsRef.current = null;
        // 컴포넌트가 아직 마운트 상태이고, 사용자가 의도적으로 닫은 게 아니며, 정상 종료(1000)가 아니면 재연결
        if (mountedRef.current && !manualCloseRef.current && e.code !== 1000) {
          const delay = Math.min(backoffRef.current, 30000);
          reconnectTimerRef.current = setTimeout(connect, delay);
          backoffRef.current = Math.min(backoffRef.current * 2, 30000);
        }
      };
    };

    connect();

    return () => {
      // 언마운트 시: 재연결 타이머 제거, 정상 종료 시도
      mountedRef.current = false;
      manualCloseRef.current = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (wsRef.current) {
        try {
          if (wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.close(1000, 'component unmount'); // 정상 종료
          } else {
            wsRef.current.close();
          }
        } catch {}
        wsRef.current = null;
      }
    };
  }, [organizationid]);

  return (
    <Snackbar open={open} autoHideDuration={6000} onClose={() => setOpen(false)}>
      <Alert severity="error" onClose={() => setOpen(false)} variant="filled">
        {msg}
      </Alert>
    </Snackbar>
  );
}
