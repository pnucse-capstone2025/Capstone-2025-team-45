import React, { useEffect, useMemo, useState, useCallback } from 'react';
import {
  Box, Stack, FormControl, InputLabel, Select, MenuItem, Typography, CircularProgress,
} from '@mui/material';
import { useTheme, alpha } from '@mui/material/styles';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip, Legend,
} from 'chart.js';

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const API_BASE = process.env.REACT_APP_API_URL;
const EVENT_TYPES = ['logon', 'email', 'http', 'device', 'file'];

async function fetchAvailableMonths() {
  const res = await fetch(`${API_BASE}/behavior-log/monthly-type-counts`);
  if (!res.ok) throw new Error('월별 유형 집계 조회 실패');
  const rows = await res.json(); // [{month:"YYYY-MM", event_type, count}, ...]
  const months = [...new Set((rows || []).map(r => r.month))];
  months.sort();
  return months;
}

// 주차별 집계 API
async function fetchWeeklyCounts({ month }) {
  const url = new URL(`${API_BASE}/behavior-log/monthly-type-counts`);
  const mm = String(month).includes('-') ? String(month).split('-')[1] : String(month);
  url.searchParams.set('month', String(Number(mm))); // '08' -> 8
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error('주차별 집계 조회 실패');
  return res.json();
}

export default function WeeklyStackedLogByMonth() {
  const theme = useTheme();
  const TYPE_COLORS = {
    logon: '#2196f3',
    email: '#4caf50',
    http: '#f44336',
    device: '#ff9800',
    file: '#9c27b0',
  };

  const [months, setMonths] = useState([]);
  const [month, setMonth] = useState('');
  const [loading, setLoading] = useState(true);
  const [optLoading, setOptLoading] = useState(true);
  const [error, setError] = useState('');
  const [labels, setLabels] = useState([]);
  const [series, setSeries] = useState({});

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setOptLoading(true);
        const ms = await fetchAvailableMonths();
        if (!mounted) return;
        setMonths(ms);
        if (ms.length) {
          setMonth(ms[ms.length - 1]); // 최신 달 자동 선택
        }
      } catch (e) {
        setError(e?.message || '월 옵션 조회 오류');
      } finally {
        setOptLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  // 차트 데이터 로딩
  const loadChart = useCallback(async (m) => {
    try {
      setLoading(true);
      setError('');
      const { weeks = [], counts = {} } = await fetchWeeklyCounts({ month: m });
      setLabels(weeks.map(w => `${w}주차`));
      setSeries(counts || {});
    } catch (e) {
      setError(e?.message || '집계 조회 오류');
      setLabels([]);
      setSeries({});
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (month) loadChart(month);
  }, [month, loadChart]);

  const suggestedMax = useMemo(() => {
    const allVals = EVENT_TYPES.flatMap(t => series[t] || []);
    const max = allVals.length ? Math.max(...allVals) : 0;
    if (max === 0) return undefined;
    const pow10 = Math.pow(10, Math.max(0, String(Math.floor(max)).length - 1));
    const step = pow10 / 2;
    return Math.ceil((max * 1.15) / step) * step;
  }, [series]);

  const chartData = useMemo(() => ({
    labels,
    datasets: EVENT_TYPES.map((t) => ({
      type: 'bar',
      label: t,
      data: series[t] || [],
      backgroundColor: TYPE_COLORS[t],
      borderColor: TYPE_COLORS[t],
      hoverBackgroundColor: alpha(TYPE_COLORS[t], 0.9),
      hoverBorderColor: TYPE_COLORS[t],
      borderWidth: 1,
      barThickness: 8,
      categoryPercentage: 0.6,
    })),
  }), [labels, series]);

  const optionsChart = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,

    plugins: {
      legend: { position: 'bottom', align: 'center', labels: { padding: 8, boxHeight: 10, boxWidth: 10 }, },
      tooltip: { mode: 'index', intersect: false, },
    },
    scales: {
      x: {
        stacked: false,
        offset: true,
        ticks: { padding: 8 },
      },
      y: {
        stacked: false,
        beginAtZero: true,
        ticks: { precision: 0, padding: 8 },
        title: { display: true, text: '개수' },
        grace: '5%',
      },
    },
  }), [suggestedMax]);

  return (
    <Box sx={{ width: '100%', height: '100%', minWidth: 0, display: 'flex' }}>
      <Box
        sx={{
          flex: '0 0 100px',
          display: { xs: 'block', md: 'flex' },
          flexDirection: 'column',
        }}
      >
        <Stack direction="column" sx={{ mb: 2 }} flex="0 0 auto">
          <FormControl size="small" fullWidth>
            <InputLabel id="month-label" sx={{
              color: '#000 !important',
              '&.Mui-focused': { color: '#000' },
              '&.MuiFormLabel-filled': { color: '#000' },
            }}>월</InputLabel>
            <Select
              labelId="month-label" label="월" value={month}
              onChange={(e) => setMonth(e.target.value)}
              sx={{
                color: '#000',
                '& .MuiSelect-select': { color: '#000 !important' },
                '& .MuiOutlinedInput-input': { color: '#000 !important' },
                '& .MuiInputBase-input': { color: '#000 !important' },
                '.MuiSelect-icon': { color: '#000' },
                '& .MuiOutlinedInput-notchedOutline': { borderColor: '#fff' },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#fff' },
                '&.Mui-focused.MuiOutlinedInput-root': {
                  outline: 'none',
                  boxShadow: 'none',
                },
              }}
              renderValue={(v) => <span style={{ color: '#000' }}>{v ?? ''}</span>}
            >
              {months.map((m) => (
                <MenuItem key={m} value={m}>{m}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </Box>

      <Box sx={{ position: 'relative', flex: '1 1 auto', minHeight: 280 }}>
        {(loading || optLoading) && (
          <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1, bgcolor: 'rgba(255,255,255,0.6)' }}>
            <CircularProgress size={28} />
          </Box>
        )}
        {error && <Typography color="error" sx={{ mb: 1 }}>{error}</Typography>}
        <Box sx={{ width: '100%', height: '100%' }}>
          <Bar data={chartData} options={optionsChart} />
        </Box>
      </Box>
    </Box>
  );
}