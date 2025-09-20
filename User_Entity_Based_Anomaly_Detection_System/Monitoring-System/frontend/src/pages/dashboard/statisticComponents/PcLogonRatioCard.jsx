// PcLogonRatioCard.jsx
import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, Box, Typography, LinearProgress, Tooltip } from '@mui/material';
import { get_pc_counts } from '../../../api/dashboard'
import { useParams } from 'react-router-dom';

const PcLogonRatioCard = () => {
  const { oid } = useParams();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({ logon_percent: 0, logon_pc_count: 0, logout_pc_count: 0 });

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    get_pc_counts(oid)
      .then(data => { if (mounted) setSummary(data); })
      .catch(() => { if (mounted) setSummary({ logon_percent: 0, logon_pc_count: 0, logout_pc_count: 0 }); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [oid]);

  const total = summary.logon_pc_count + summary.logout_pc_count;

  // 바/라벨용 비율 계산 (0~100)
  const ratioNum = useMemo(() => {
    if (total > 0) {
      return Math.min(
        100,
        Math.max(0, (summary.logon_pc_count / total) * 100)
      );
    }
    // total이 0이면 API의 logon_percent 사용 (0~1 또는 0~100 둘 다 허용)
    if (typeof summary.logon_percent === 'number') {
      const p = summary.logon_percent;
      const pct = p <= 1 ? p * 100 : p; // 0~1이면 100배, 0~100이면 그대로
      return Math.min(100, Math.max(0, pct));
    }
    return 0;
  }, [summary.logon_pc_count, total, summary.logon_percent]);

  const ratioLabel = useMemo(() => `${ratioNum.toFixed(2)}%`, [ratioNum]);

  return (
    <Card variant="outlined" sx={{ height: '100%', backgroundColor: '#fff', color: '#000' }}>
      <CardContent>
        <Box className="flex justify-between items-start mb-2">
          <Typography variant="subtitle2" sx={{ color: '#000' }}>
            로그온 PC 비율
          </Typography>
          {!!total && (
            <Typography variant="caption" sx={{ color: '#000' }}>
              {summary.logon_pc_count}/{total}
            </Typography>
          )}
        </Box>

        {loading ? (
          <Box className="flex justify-center items-center h-28">
            <Typography variant="body2" sx={{ color: '#000' }}>Loading...</Typography>
          </Box>
        ) : (
          <Box>
            <Box className="flex items-baseline gap-2 mb-1">
              <Typography variant="h3" fontWeight={700} sx={{ color: '#000' }}>
                {ratioLabel}
              </Typography>
              <Tooltip title="로그온 PC / 전체 PC">
                <Typography variant="body2" sx={{ color: '#000' }}>
                  ({summary.logon_pc_count}/{total || 0})
                </Typography>
              </Tooltip>
            </Box>

            <LinearProgress
              variant="determinate"
              value={ratioNum}      // <-- 숫자!
              sx={{
                height: 10,
                borderRadius: 9999,
                mt: 1.5,
                backgroundColor: '#e0e0e0',
                '& .MuiLinearProgress-bar': { backgroundColor: '#1976d2' },
              }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default PcLogonRatioCard;
