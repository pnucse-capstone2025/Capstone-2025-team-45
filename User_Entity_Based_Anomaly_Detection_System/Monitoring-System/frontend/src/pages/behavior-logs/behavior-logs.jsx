import React, { useEffect, useMemo, useState } from 'react';
import {
  Box, Autocomplete, TextField, IconButton, Popover, List, ListItemButton, ListItemText,
  Chip, Stack, Typography, Divider, Paper, TableContainer, Table, TableHead, TableRow,
  TableCell, TableBody, TableFooter, TablePagination, GlobalStyles, CircularProgress,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';

import SortIcon from '@mui/icons-material/SwapVert';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import RefreshIcon from '@mui/icons-material/Refresh';

import {
  fetchBehaviorLogs,
  fetchBehaviorFacets,
} from '../../services/BehaviorLogsService';

// ---------- utils ----------
const EVENT_TYPES = ['logon', 'email', 'http', 'device', 'file'];
const compare = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

const splitEmails = (raw) => {
  if (Array.isArray(raw)) raw = raw.filter((v) => v != null).map(String).join(',');
  else if (typeof raw !== 'string') {
    if (raw == null || Number.isNaN(raw)) return [];
    raw = String(raw);
  }
  const s = raw.trim();
  if (!s || s.toLowerCase() === 'nan') return [];
  return s
    .replace(/\r?\n/g, ' ')
    .split(/[,;]+/g)
    .map((v) => v.trim().replace(/^[({\[]+|[)\}\]]+$/g, ''))
    .filter(Boolean);
};

const formatBytes = (n) => {
  if (!Number.isFinite(n)) return null;
  const u = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0, v = n;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  const num = v < 10 && i > 0 ? v.toFixed(1) : Math.round(v);
  return `${num} ${u[i]}`;
};

const parseAddress = (s = '') => {
  const m = s.match(/^\s*"?([^"<]*)"?\s*<([^>]+)>\s*$/);
  return m ? { name: m[1].trim(), email: m[2].trim() } : { name: '', email: s.trim() };
};

const shortEmail = (addr, maxLen = 16, reserve = 0) => {
  if (!addr) return '-';
  const { name, email } = parseAddress(addr);
  const budget = Math.max(8, maxLen - reserve);
  if (name && name.length <= Math.min(12, budget)) return name;
  const show = email || addr;
  if (show.length <= budget) return show;
  const [local, domainFull] = show.split('@');
  if (!domainFull) return show.slice(0, budget - 1) + '…';
  const keepL = Math.min(4, Math.max(2, Math.floor(local.length * 0.3)));
  const keepR = Math.min(2, Math.max(1, Math.floor(local.length * 0.15)));
  let out = `${local.slice(0, keepL)}…${local.slice(-keepR)}@${domainFull}`;
  if (out.length > budget) {
    const parts = domainFull.split('.');
    const tld = parts.pop() || '';
    const sld = (parts.pop() || '').slice(0, 3);
    const domShort = (sld ? `${sld}…` : '') + (tld ? `.${tld}` : '');
    out = `${local.slice(0, keepL)}…${local.slice(-keepR)}@${domShort}`;
  }
  return out.length <= budget ? out : out.slice(0, budget - 1) + '…';
};

const asDash = (v, fmt = (x) => x) => (Number.isFinite(v) ? fmt(v) : '-');

// ---------- 페이지네이션 액션 ----------
function PagerActions({ page, rowsPerPage, onPageChange, hasMore, total }) {
  const knownTotal = Number.isFinite(total);
  const lastPage = knownTotal ? Math.max(0, Math.ceil(total / rowsPerPage) - 1) : null;
  const disablePrev = page === 0;
  const disableNext = knownTotal ? page >= lastPage : !hasMore;
  return (
    <Box sx={{ flexShrink: 0, ml: 1 }}>
      <IconButton onClick={(e) => onPageChange(e, page - 1)} disabled={disablePrev} size="small">
        <ChevronLeftIcon fontSize="small" />
      </IconButton>
      <IconButton onClick={(e) => onPageChange(e, page + 1)} disabled={disableNext} size="small">
        <ChevronRightIcon fontSize="small" />
      </IconButton>
    </Box>
  );
}

// ---------- 이벤트 타입 선택자 ----------
const EventTypeSelector = ({ value, onChange }) => {
  const handleToggle = (type) => {
    if (type === 'all') {
      onChange(['all']);
      return;
    }
    const hasAll = value.includes('all');
    let next = hasAll ? [] : [...value];
    if (next.includes(type)) next = next.filter((t) => t !== type);
    else next.push(type);
    const uniqueSelected = next.filter((t) => EVENT_TYPES.includes(t));
    if (uniqueSelected.length === EVENT_TYPES.length) onChange(['all']);
    else if (uniqueSelected.length === 0) onChange(['all']);
    else onChange(uniqueSelected);
  };
  const isChecked = (type) => (value.includes('all') ? type === 'all' : value.includes(type));
  const chipSx = (selected) => ({
    bgcolor: 'transparent',
    borderWidth: 1.5,
    borderColor: selected ? 'primary.main' : 'transparent',
    color: selected ? 'primary.main' : 'text.secondary',
  });
  return (
    <Stack direction="row" spacing={1} flexWrap="wrap">
      <Chip label="All" variant="outlined" sx={chipSx(isChecked('all'))} onClick={() => handleToggle('all')} />
      {EVENT_TYPES.map((t) => (
        <Chip key={t} label={t} variant="outlined" sx={chipSx(isChecked(t))} onClick={() => handleToggle(t)} />
      ))}
    </Stack>
  );
};

// ---------- 세부사항 필드 ----------
const DetailCell = ({ row }) => {
  const [hover, setHover] = React.useState(false);
  const [httpAnchorPos, setHttpAnchorPos] = React.useState(null);
  const [emailAnchorPos, setEmailAnchorPos] = React.useState(null);
  const iconRef = React.useRef(null);

  const Line = ({ children, onIconClick }) => (
    <Box
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      sx={{ display: 'grid', gridTemplateColumns: '28px 1fr 28px', alignItems: 'center', width: '100%' }}
    >
      <Box aria-hidden sx={{ width: 28 }} />
      <Typography variant="body2" noWrap sx={{ minWidth: 0, textAlign: 'center' }}>
        {children}
      </Typography>
      <IconButton
        size="small"
        ref={iconRef}
        onClick={(e) => {
          e.stopPropagation();
          onIconClick?.();
        }}
        aria-label="Show details"
        title="Show details"
        sx={{
          justifySelf: 'end',
          p: 0.5,
          opacity: hover || Boolean(emailAnchorPos) || Boolean(httpAnchorPos) ? 1 : 0,
          pointerEvents: hover || Boolean(emailAnchorPos) || Boolean(httpAnchorPos) ? 'auto' : 'none',
          transition: 'opacity .15s ease',
        }}
      >
        <VisibilityOutlinedIcon fontSize="inherit" />
      </IconButton>
    </Box>
  );

  const FieldRow = ({ label, value }) => (
    <Box sx={{ display: 'grid', gridTemplateColumns: '50px 1fr', columnGap: 1, alignItems: 'baseline' }}>
      <Typography sx={{ color: 'text.secondary', fontWeight: 700 }}>{label}</Typography>
      <Typography sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{value}</Typography>
    </Box>
  );

  if (row.event_type === 'http' && row.url) {
    const host = (() => {
      try { return new URL(row.url).host; } catch { return row.url; }
    })();
    return (
      <>
        <Line
          onIconClick={() => {
            const r = iconRef.current?.getBoundingClientRect();
            if (!r) return;
            setHttpAnchorPos({ left: Math.round(r.left + r.width / 2), top: Math.round(r.bottom) });
          }}
        >
          {host}
        </Line>
        <Popover
          open={Boolean(httpAnchorPos)}
          onClose={() => setHttpAnchorPos(null)}
          anchorReference="anchorPosition"
          anchorPosition={httpAnchorPos || { top: -9999, left: -9999 }}
          container={document.body}
          slotProps={{
            paper: { elevation: 0, sx: { p: 1.5, maxWidth: 560, bgcolor: '#000', boxShadow: '0 16px 48px rgba(0,0,0,.5)' } },
          }}
        >
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>Full URL</Typography>
          <Typography sx={{ whiteSpace: 'normal', wordBreak: 'break-all' }}>{row.url}</Typography>
        </Popover>
      </>
    );
  }

  if (row.event_type === 'email') {
    const to = splitEmails(row.to);
    const moreTo = Math.max(0, to.length - 1);
    const suffixLen = moreTo > 0 ? ` (+${moreTo})`.length : 0;
    const firstTo = shortEmail(to[0], 22, suffixLen);
    const cc = splitEmails(row.cc);
    const bcc = splitEmails(row.bcc);
    const attLabel = asDash(row.attachment, (x) => x);
    const sizeLabel = asDash(row.email_size, formatBytes);
    const label = `${firstTo || '-'}${moreTo > 0 ? ` (+${moreTo})` : ''}`;
    return (
      <>
        <Line
          onIconClick={() => {
            const r = iconRef.current?.getBoundingClientRect();
            if (!r) return;
            setEmailAnchorPos((prev) => (prev ? null : { left: Math.round(r.left + r.width / 2), top: Math.round(r.bottom) }));
          }}
        >
          <span title={to.join('; ') || '-'}>{label}</span>
        </Line>
        <Popover
          open={Boolean(emailAnchorPos)}
          onClose={() => setEmailAnchorPos(null)}
          anchorReference="anchorPosition"
          anchorPosition={emailAnchorPos || { top: -9999, left: -9999 }}
          container={document.body}
          slotProps={{
            paper: {
              elevation: 0,
              sx: { p: 1.5, maxWidth: 720, bgcolor: '#000', boxShadow: '0 16px 48px rgba(0,0,0,.5)', borderRadius: 1.2 },
            },
          }}
        >
          <Stack spacing={1}>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>Email details</Typography>
            <FieldRow label="From:" value={row.from_addr || '-'} />
            <FieldRow label="To:" value={to.length ? to.join('\n') : '-'} />
            <FieldRow label="Cc:" value={cc.length ? cc.join('\n') : '-'} />
            <FieldRow label="Bcc:" value={bcc.length ? bcc.join('\n') : '-'} />
            <FieldRow label="Att:" value={String(attLabel)} />
            <FieldRow label="Size:" value={String(sizeLabel)} />
          </Stack>
        </Popover>
      </>
    );
  }

  if (row.event_type === 'file')   return <Typography variant="body2" noWrap sx={{ display: 'block', textAlign: 'center' }}>{row.filename}</Typography>;
  if (row.event_type === 'device') return <Typography variant="body2" noWrap sx={{ display: 'block', textAlign: 'center' }}>{row.device_activity}</Typography>;
  if (row.event_type === 'logon')  return <Typography variant="body2" noWrap sx={{ display: 'block', textAlign: 'center' }}>{row.logon_activity}</Typography>;
  return <Typography variant="body2" noWrap sx={{ display: 'block', textAlign: 'center' }}>{row.summary}</Typography>;
};

// ---------- 메인 컴포넌트 ----------
const BehaviorLogs = () => {
  const theme = useTheme();

  const [rawLogs, setRawLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(null);
  const [hasMore, setHasMore] = useState(false);

  const [department, setDepartment] = useState(null);
  const [team, setTeam] = useState(null);
  const [employee, setEmployee] = useState(null);

  const [eventTypes, setEventTypes] = useState(['all']);

  const DEFAULT_SORT_PREF = { time: 'desc', department: 'asc', team: 'asc', user: 'asc' };
  const [sortPref, setSortPref] = useState(DEFAULT_SORT_PREF);
  const [sortKey, setSortKey] = useState('time');      // time | department | team | user
  const [sortOrder, setSortOrder] = useState(DEFAULT_SORT_PREF.time);
  const [sortAnchor, setSortAnchor] = useState(null);

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const [dateFrom, setDateFrom] = useState(null);
  const [dateTo, setDateTo] = useState(null);
  const [rangeDigits, setRangeDigits] = useState('');
  const [isPeriodFocused, setIsPeriodFocused] = useState(false);
  const [refreshFlag, setRefreshFlag] = useState(0);

  const handleRefresh = () => {
    pageCache.current = new Map();
    cursorsRef.current = new Map([[0, null]]);
    setPage(0);
    setRefreshFlag((v) => v + 1);
  };

  const headRowRef = React.useRef(null);
  const firstBodyRowRef = React.useRef(null);
  const [headH, setHeadH] = useState(44);
  const [rowH, setRowH] = useState(42);

  const VISIBLE = 10;  // 화면에 고정으로 보여줄 행 수
  const PAG_H = 36;    // TablePagination 대략 높이
  const tableHeight = headH + rowH * VISIBLE + PAG_H;

  const footerRef = React.useRef(null);
  const [footerH, setFooterH] = useState(0);
  React.useLayoutEffect(() => {
    const measure = () => setFooterH(footerRef.current?.offsetHeight || 0);
    measure();
    const ro = new ResizeObserver(measure);
    if (footerRef.current) ro.observe(footerRef.current);
    window.addEventListener('resize', measure);
    return () => { ro.disconnect(); window.removeEventListener('resize', measure); };
  }, []);

  const pageCache = React.useRef(new Map());
  const cursorsRef = React.useRef(new Map());
  if (!cursorsRef.current.has(0)) cursorsRef.current.set(0, null);

  const makeKey = (p) =>
    JSON.stringify({
      department, team, employee, eventTypes,
      sortKey, sortOrder, dateFrom, dateTo, p, rowsPerPage, refreshFlag,
    });

  useEffect(() => {
    const key = makeKey(page);
    setLoading(true);

    const cached = pageCache.current.get(key);
    if (cached) {
      setRawLogs(cached.items);
      if (Number.isFinite(cached.total)) setTotal(cached.total);
    }

    const cursor = cursorsRef.current.get(page) || null;
    const params = {
      limit: rowsPerPage,
      department, team, user: employee,
      sortKey, sortOrder, // ⬅ 서버가 전체 데이터 기준으로 정렬하도록 전달
      eventTypes, dateFrom, dateTo,
      includeTotal: false, cursor, offset: page * rowsPerPage,
    };

    fetchBehaviorLogs(params)
      .then(({ items, total: resTotal, hasMore: resHasMore, nextCursor }) => {
        setRawLogs(items);
        if (Number.isFinite(resTotal)) setTotal(resTotal);
        setHasMore(resHasMore);
        pageCache.current.set(key, { items, total: resTotal });

        if (nextCursor) cursorsRef.current.set(page + 1, nextCursor);

        if (page === 0) {
          fetchBehaviorLogs({ ...params, cursor: null, offset: 0, limit: 1, includeTotal: true })
            .then(({ total }) => { if (Number.isFinite(total)) setTotal(total); })
            .catch(() => {});
        }
      })
      .finally(() => setLoading(false));
  }, [department, team, employee, eventTypes, sortKey, sortOrder, dateFrom, dateTo, page, rowsPerPage, refreshFlag]);

  // 필터/정렬/기간 바뀌면 페이지/캐시 리셋
  useEffect(() => {
    pageCache.current = new Map();
    cursorsRef.current = new Map([[0, null]]);
    setPage(0);
  }, [department, team, employee, eventTypes, sortKey, sortOrder, dateFrom, dateTo]);

  // Facets 로드
  const [depOptions, setDepOptions] = useState([]);
  const [teamOptions, setTeamOptions] = useState([]);
  const [empOptions, setEmpOptions] = useState([]);
  useEffect(() => {
    let alive = true;
    const timer = setTimeout(() => {
      fetchBehaviorFacets({ department, team, dateFrom, dateTo, eventTypes })
        .then(({ departments, teams, employees }) => {
          if (!alive) return;
          setDepOptions(departments);
          setTeamOptions(teams);
          setEmpOptions(employees);
        })
        .catch(() => {
          if (alive) { setDepOptions([]); setTeamOptions([]); setEmpOptions([]); }
        });
    }, 150);
    return () => { alive = false; clearTimeout(timer); };
  }, [department, team, dateFrom, dateTo, eventTypes]);

  // 기간 입력
  const commitFromDigits = (digits) => {
    const a = digits.slice(0, 8);
    const b = digits.slice(8, 16);
    const from = a.length === 8 ? `${a.slice(0, 4)}-${a.slice(4, 6)}-${a.slice(6, 8)}` : null;
    const to = b.length === 8 ? `${b.slice(0, 4)}-${b.slice(4, 6)}-${b.slice(6, 8)}` : null;
    setDateFrom(from);
    setDateTo(to);
    setPage(0);
  };

  const formatTsMultiline = (ts) => {
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return String(ts);
    const pad = (n) => String(n).padStart(2, '0');
    const date = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    const time = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    return `${date}\n${time}`;
  };

  const filtered = useMemo(() => {
    const selectedSet = new Set(eventTypes.includes('all') ? EVENT_TYPES : eventTypes);
    return rawLogs.filter((l) => {
      if (department && l.department !== department) return false;
      if (team && l.team !== team) return false;
      if (employee && l.user !== employee) return false;
      if (!selectedSet.has(l.event_type)) return false;
      if (dateFrom || dateTo) {
        const ts = new Date(l.timestamp).getTime();
        if (dateFrom) {
          const fromTs = new Date(`${dateFrom}T00:00:00`).getTime();
          if (ts < fromTs) return false;
        }
        if (dateTo) {
          const toTs = new Date(`${dateTo}T23:59:59.999`).getTime();
          if (ts > toTs) return false;
        }
      }
      return true;
    });
  }, [rawLogs, department, team, employee, eventTypes, dateFrom, dateTo]);

  const viewRows = filtered;

  const openSort = (e) => setSortAnchor(e.currentTarget);
  const closeSort = () => setSortAnchor(null);

  const columns = useMemo(
    () => [
        { key: 'timestamp',  label: '시간',     width: '12%',  align: 'center' },
        { key: 'department', label: '부서',     width: '14%', align: 'center' },
        { key: 'team',       label: '팀',       width: '14%', align: 'center' },
        { key: 'user',       label: '사용자 ID',   width: '12%', align: 'center' },
        { key: 'pc_id',      label: 'PC ID',       width: '12%', align: 'center' },
        { key: 'event_type', label: '이벤트',   width: '12%', align: 'center' },
        { key: 'detail',     label: '세부사항',  width: '24%', align: 'center' },
    ],
    []
  );

  const toggleSortOrder = () => {
    const next = sortOrder === 'asc' ? 'desc' : 'asc';
    setSortOrder(next);
    setSortPref((prev) => ({ ...prev, [sortKey]: next }));
  };

  const colCount = columns.length;
  const showEmpty = !loading && viewRows.length === 0;

  return (
    <>
      <GlobalStyles
        styles={{
          'html, body, #root': { height: '100%' },
          html: { overflowX: 'hidden' },
          body: { overflowX: 'hidden' },
          '@keyframes spin': { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } },
        }}
      />
      <Box sx={{ display: 'flex', width: '100%', minWidth: 0 }}>
        <Box sx={{ flex: 1, minWidth: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {/* 필터 */}
          <Box sx={{ p: { xs: 1, md: 1.25 }, pb: 0.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Autocomplete
                options={depOptions}
                value={department}
                onChange={(_, v) => {
                  setDepartment(v);
                  setTeam(null);
                  setEmployee(null);
                  setTeamOptions([]);
                  setEmpOptions([]);
                  setPage(0);
                }}
                fullWidth
                sx={{ flex: 1, minWidth: 200 }}
                renderInput={(params) => <TextField {...params} label="부서" placeholder="부서 검색" fullWidth />}
                clearOnEscape
              />
              <Autocomplete
                options={teamOptions}
                value={team}
                onChange={(_, v) => {
                  setTeam(v);
                  setEmployee(null);
                  setEmpOptions([]);
                  setPage(0);
                }}
                fullWidth
                sx={{ flex: 1, minWidth: 200 }}
                renderInput={(params) => <TextField {...params} label="팀" placeholder="팀 검색" fullWidth />}
                clearOnEscape
              />
              <Autocomplete
                options={empOptions}
                value={employee}
                onChange={(_, v) => {
                  setEmployee(v);
                  setPage(0);
                }}
                fullWidth
                sx={{ flex: 1, minWidth: 200 }}
                renderInput={(params) => <TextField {...params} label="사용자 ID" placeholder="사용자 ID 검색" fullWidth />}
                clearOnEscape
              />

              {/* 기간 입력 */}
              <Box sx={{ position: 'relative', width: 252, display: { xs: 'none', sm: 'block' } }}>
                {isPeriodFocused && (
                  <Box
                    aria-hidden
                    sx={{
                      position: 'absolute',
                      left: 14,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      pointerEvents: 'none',
                      color: 'text.secondary',
                      zIndex: 1,
                      whiteSpace: 'pre',
                      fontFamily:
                        'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                      fontVariantNumeric: 'tabular-nums',
                    }}
                  >
                    {(() => {
                      let di = 0, dashIdx = 0, out = '';
                      const DASH = [4, 6, 12, 14];
                      const MASK = 'YYYY-MM-DD ~ YYYY-MM-DD';
                      for (const ch of MASK) {
                        if ('YMD'.includes(ch)) {
                          out += di < rangeDigits.length ? ' ' : ch;
                          if (di < rangeDigits.length) di++;
                        } else if (ch === '-') {
                          const th = DASH[dashIdx++];
                          out += rangeDigits.length > th ? ' ' : '-';
                        } else if (ch === '~') {
                          out += rangeDigits.length >= 8 ? ' ' : '~';
                        } else out += ch;
                      }
                      return out;
                    })()}
                  </Box>
                )}
                <TextField
                  label="기간"
                  value={
                    rangeDigits
                      ? (() => {
                          let di = 0, dashIdx = 0, out = '';
                          const DASH = [4, 6, 12, 14];
                          const MASK = 'YYYY-MM-DD ~ YYYY-MM-DD';
                          for (const ch of MASK) {
                            if ('YMD'.includes(ch)) {
                              out += di < rangeDigits.length ? rangeDigits[di++] : ' ';
                            } else if (ch === '-') {
                              const th = DASH[dashIdx++];
                              out += rangeDigits.length > th ? '-' : ' ';
                            } else if (ch === '~') {
                              out += rangeDigits.length >= 8 ? '~' : ' ';
                            } else out += ' ';
                          }
                          return out;
                        })()
                      : ''
                  }
                  onFocus={() => setIsPeriodFocused(true)}
                  onBlur={() => { setIsPeriodFocused(false); commitFromDigits(rangeDigits); }}
                  onKeyDown={(e) => {
                    if (/^[0-9]$/.test(e.key)) {
                      e.preventDefault();
                      setRangeDigits((prev) => {
                        if (prev.length >= 16) return prev;
                        const next = prev + e.key;
                        if (next.length === 16) commitFromDigits(next);
                        return next;
                      });
                      return;
                    }
                    if (e.key === 'Backspace') { e.preventDefault(); setRangeDigits((prev) => prev.slice(0, -1)); return; }
                    if (e.key === 'Delete')   { e.preventDefault(); return; }
                    if (e.key === 'Enter')    { e.preventDefault(); commitFromDigits(rangeDigits); }
                    if (['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(e.key)) e.preventDefault();
                  }}
                  onPaste={(e) => {
                    e.preventDefault();
                    const digits = (e.clipboardData.getData('text') || '').replace(/\D/g, '').slice(0, 16);
                    setRangeDigits(digits);
                    if (digits.length === 16) commitFromDigits(digits);
                  }}
                  inputProps={{
                    readOnly: true, spellCheck: false, autoComplete: 'off',
                    style: {
                      fontFamily:
                        'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                      fontVariantNumeric: 'tabular-nums',
                      caretColor: 'transparent', position: 'relative', zIndex: 2, background: 'transparent',
                    },
                  }}
                  sx={{ width: '100%' }}
                />
              </Box>

              <IconButton
                size="small"
                onClick={(e) => setSortAnchor(e.currentTarget)}
                aria-label="정렬 옵션"
                title="정렬"
                sx={{
                  ml: 'auto',
                  border: '1.5px solid',
                  borderColor: 'divider',
                  color: 'primary.main',
                  '& svg': { fontSize: 18 },
                }}
              >
                <SortIcon fontSize="small" />
              </IconButton>

              <IconButton
              size="small"
              onClick={handleRefresh}
              title="새로고침"
              aria-label="새로고침"
              disabled={loading}
              sx={{
                ml: 0.5,
                border: '1.5px solid',
                borderColor: 'divider',
                color: 'text.black',
                '& .MuiSvgIcon-root': {
                    fontSize: 18,
                    animation: loading ? 'spin .8s linear infinite' : 'none',
                  },
                  '&.Mui-disabled': {
                    opacity: 1,
                    color: 'text.secondary',
                    borderColor: 'divider',
                  },
              }}
            >
              <RefreshIcon fontSize="small" />
              </IconButton>
            </Box>

            <Popover
              open={Boolean(sortAnchor)}
              anchorEl={sortAnchor}
              onClose={() => setSortAnchor(null)}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              transformOrigin={{ vertical: 'top', horizontal: 'right' }}
              slotProps={{ paper: { sx: { mt: 0.5, zIndex: (t) => t.zIndex.modal + 1 } } }}
              container={document.body}
            >
              <Box p={1} minWidth={220}>
                <Stack direction="row" alignItems="center" justifyContent="space-between" px={1} pb={1}>
                  <Typography variant="subtitle2">정렬 옵션</Typography>
                  <IconButton size="small" onClick={toggleSortOrder}>
                    {sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />}
                  </IconButton>
                </Stack>
                <Divider />
                <List dense sx={{ py: 0 }}>
                  {[
                    { key: 'time', label: '시간순' },
                    ...(employee
                      ? []
                      : team
                      ? [{ key: 'user', label: '사용자' }]
                      : department
                      ? [
                          { key: 'team', label: '팀명' },
                          { key: 'user', label: '사용자' },
                        ]
                      : [
                          { key: 'department', label: '부서명' },
                          { key: 'team', label: '팀명' },
                          { key: 'user', label: '사용자' },
                        ]),
                  ].map((opt) => (
                    <ListItemButton
                      key={opt.key}
                      selected={sortKey === opt.key}
                      onClick={() => {
                        setSortKey(opt.key);
                        setSortOrder(sortPref[opt.key] ?? (opt.key === 'time' ? 'desc' : 'asc'));
                        setSortAnchor(null);
                    }}
                    >
                      <ListItemText primary={opt.label} />
                    </ListItemButton>
                  ))}
                </List>
              </Box>
            </Popover>

            <Divider sx={{ my: 1 }} />
            <Box sx={{ px: 1, py: 0.75 }}>
              <Stack direction="row" alignItems="center" spacing={1.25} sx={{ flexWrap: 'wrap' }}>
                <Typography variant="subtitle2" minWidth={88} textAlign="center">이벤트 타입:</Typography>
                <EventTypeSelector
                  value={eventTypes}
                  onChange={(v) => { setEventTypes(v); setPage(0); }}
                />
              </Stack>
            </Box>
          </Box>

          {/* 테이블 */}
          <Box sx={{ px: { xs: 1, md: 1.25 }, pb: 0.25, flex: 1, minHeight: 0, display: 'flex' }}>
            <Paper
              variant="outlined"
              sx={{
                borderRadius: 2,
                borderColor: 'divider',
                bgcolor: 'transparent',
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                minHeight: 0,
                overflow: 'hidden',
              }}
            >
              <TableContainer
                sx={{
                  position: 'relative',
                  flex: 1,
                  minHeight: 0,
                  overflowX: 'auto',
                  overflowY: 'auto',
                  backgroundColor: 'transparent',
                }}
                aria-busy={loading}
              >
                {(loading || showEmpty) && (
                  <Box
                    sx={{
                      position: 'absolute',
                      left: 0,
                      right: 0,
                      top: 0,
                      bottom: `${footerH}px`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: 'background.white',
                      opacity: 0.9,
                      zIndex: 2,
                      color: 'text.black',
                      textAlign: 'center',
                    }}
                    role="status"
                  >
                    {loading ? (
                      <>
                        <CircularProgress size={20} sx={{ mr: 1 }} />
                        <Typography variant="body2">Loading…</Typography>
                      </>
                    ) : (
                      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        No data
                      </Typography>
                    )}
                  </Box>
                )}
                <Table
                  size="small"
                  stickyHeader
                  sx={{
                    tableLayout: 'fixed',
                    width: '100%',
                    fontSize: { xs: 12.5, md: 13.5 },
                    '& .MuiTableCell-root': {
                      py: { xs: 0.6, md: 0.75 },
                      px: { xs: 0.75, md: 1 },
                      backgroundColor: 'background.paper',
                      color: 'text.primary',
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                      whiteSpace: 'normal',
                      overflowWrap: 'anywhere',
                      wordBreak: 'break-word',
                    },
                    '& thead .MuiTableCell-root': { backgroundColor: 'background.default', fontWeight: 700 },
                    '& tbody .MuiTableRow-root:nth-of-type(odd) .MuiTableCell-root': { backgroundColor: 'rgba(255,255,255,0.03)', color: 'text.black' },
                    '& tbody .MuiTableRow-root:nth-of-type(even) .MuiTableCell-root': { backgroundColor: 'transparent', color: 'text.black' },
                    '& tbody .MuiTableRow-root:hover .MuiTableCell-root': { backgroundColor: '#e0e0e0' },
                    '& tbody .MuiTableCell-root:first-of-type': { fontVariantNumeric: 'tabular-nums' },
                    '& tbody .MuiTableRow-root:last-of-type .MuiTableCell-root': { borderBottom: 'none' },
                  }}
                >
                  <colgroup>
                    {columns.map((c) => (
                      <col key={c.key} style={c.width ? { width: c.width } : undefined} />
                    ))}
                  </colgroup>
                  <TableHead>
                    <TableRow>
                      {columns.map((c) => (
                        <TableCell key={c.key} style={{ width: c.width }} align={c.align || 'left'}>
                          {c.label}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {viewRows.map((row, idx) => (
                      <TableRow key={`${row.id ?? 'noid'}-${row.timestamp ?? 'ts'}-${idx}`} hover>
                        {/* 공통 셀들: 열 구성에 따라 렌더 */}
                        {columns.map((c) => {
                          const key = c.key;
                          if (key === 'timestamp') {
                            return (
                              <TableCell key={key} sx={{ whiteSpace: 'pre-line !important', lineHeight: 1.2, textAlign: 'center' }}>
                                {formatTsMultiline(row.timestamp)}
                              </TableCell>
                            );
                          }
                          if (key === 'department') return <TableCell key={key}>{row.department}</TableCell>;
                          if (key === 'team')        return <TableCell key={key}>{row.team}</TableCell>;
                          if (key === 'user')        return <TableCell key={key} sx={{ lineHeight: 1.2 }}>{row.user}</TableCell>;
                          if (key === 'pc_id')       return <TableCell key={key}>{row.pc_id}</TableCell>;
                          if (key === 'event_type')  return <TableCell key={key}>{row.event_type}</TableCell>;
                          if (key === 'detail') {
                            return (
                              <TableCell key={key} align="center" sx={{ position: 'relative', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: { xs: 320, md: 460, lg: 520 }, }}>
                                <DetailCell row={row} />
                              </TableCell>
                            );
                          }
                          return null;
                        })}
                      </TableRow>
                    ))}
                  </TableBody>

                  {/* 페이징 */}
                  <TableFooter
                    sx={{
                      '& .MuiTableCell-root': { p: 0 },
                      '& .MuiTableCell-sizeSmall': { p: 0 },
                    }}
                  >
                    <TableRow>
                      <TableCell ref={footerRef} colSpan={colCount} sx={{ p: 0 }}>
                        <TablePagination
                          component="div"
                          count={Number.isFinite(total) ? total : -1}
                          page={page}
                          onPageChange={(_, p) => setPage(p)}
                          rowsPerPage={rowsPerPage}
                          rowsPerPageOptions={[]}
                          labelRowsPerPage=""
                          labelDisplayedRows={({ from, to, count }) => `${from}-${to} of ${count === -1 ? '…' : count}`}
                          ActionsComponent={(subProps) => <PagerActions {...subProps} hasMore={hasMore} total={total} />}
                          sx={{
                            m: 0,
                            borderTop: '1px solid',
                            borderColor: 'divider',
                            '.MuiTablePagination-toolbar': { minHeight: 36, px: { xs: .5, md: 1 }, py: 0, backgroundColor: 'background.default' },
                            '.MuiTablePagination-actions': { ml: 0 },
                          }}
                        />
                      </TableCell>
                    </TableRow>
                  </TableFooter>
                </Table>
              </TableContainer>
            </Paper>
          </Box>
        </Box>
      </Box>
    </>
  );
};

export default BehaviorLogs;
