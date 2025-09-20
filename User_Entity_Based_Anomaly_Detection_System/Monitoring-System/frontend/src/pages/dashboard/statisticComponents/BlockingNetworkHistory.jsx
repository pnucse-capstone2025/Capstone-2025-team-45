import React, { useEffect, useState } from 'react';
import { Box, Table, TableBody, TableCell, TableHead, TableRow, CircularProgress } from '@mui/material';
import CommonCard from '../../../components/common/card/CommonCard';
import { fetchNetworkBlockingLogs } from '../../../api/dashboard';
import { useParams } from 'react-router-dom';
import { useTheme } from '@mui/material/styles';

const BlockingNetworkHistory = () => {
  const { oid } = useParams();
  const theme = useTheme();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await fetchNetworkBlockingLogs(oid);
        setLogs(data.results || []);
      } catch (error) {
        console.error('차단 기록 데이터를 가져오는 데 실패했습니다:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [oid]);

  return (
    <CommonCard title="네트워크 차단 기록">
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" height={150}>
          <CircularProgress />
        </Box>
      ) : (
        <Box height={300} overflow="auto">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>기록 ID</TableCell>
                <TableCell>사용자 ID</TableCell>
                <TableCell>PC ID</TableCell>
                <TableCell>로그온 시간</TableCell>
                <TableCell>차단 시간</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((row) => (
                <TableRow key={row.blocking_history_id}>
                  <TableCell sx={{ color: theme.palette.text.black }}>{row.blocking_history_id}</TableCell>
                  <TableCell sx={{ color: theme.palette.text.black }}>{row.employee_id}</TableCell>
                  <TableCell sx={{ color: theme.palette.text.black }}>{row.pc_id}</TableCell>
                  <TableCell sx={{ color: theme.palette.text.black }}>{row.logon_time?.replace('T', ' ')}</TableCell>
                  <TableCell sx={{ color: theme.palette.text.black }}>{row.blocking_time?.replace('T', ' ')}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}
    </CommonCard>
  );
};

export default BlockingNetworkHistory;
