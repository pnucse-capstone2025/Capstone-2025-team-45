import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTheme } from '@emotion/react';
import { Box, Table, TableBody, TableCell, TableHead, TableRow, CircularProgress } from '@mui/material';
import CommonCard from '../../components/common/card/CommonCard';
import { getPcsStatus, ControlPCNetwork } from '../../api/pctable';
import RefreshIcon from '@mui/icons-material/Refresh';

const PcsStatusTable = () => {
    const theme = useTheme();
    const [pcs, setPcs] = useState([]);
    const [loading, setLoading] = useState(true);
    const oid = useParams().oid;

    const fetchPcs = () => {
        setLoading(true);
        getPcsStatus({ organizationid: oid })
            .then((data) => setPcs(data))
            .catch((err) => console.error('PC 상태 조회 실패:', err))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchPcs();
    }, [oid]);

    const BlockPCNetwork = async (pcId, block) => {
        try {
            await ControlPCNetwork({ organization_id: oid, pc_id: pcId, access_flag: block });
            fetchPcs();
        } catch (err) {
            alert('PC 네트워크 제어 실패');
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" height={200}>
                <CircularProgress />
            </Box>
        );
    }
    return (
        <Table 
            size="small"
            sx={{
                '& thead th': {
                    backgroundColor: theme.palette.primary.main,
                    color: theme.palette.common.white,
                    fontWeight: 700,
                }
            }}
        >
            <TableHead>
                <TableRow>
                    <TableCell>PC ID</TableCell>
                    <TableCell>IP 주소</TableCell>
                    <TableCell>MAC 주소</TableCell>
                    <TableCell>상태</TableCell>
                    <TableCell>사용자</TableCell>
                    <TableCell>네트워크 접근</TableCell>
                    <TableCell>액션</TableCell>
                </TableRow>
            </TableHead>
            <TableBody
                sx={{
                    '& thead th': { color: theme.palette.primary.dark, fontWeight: 700 },
                    '& tbody td': { color: theme.palette.text.black },
                }}
            >
                {pcs.map((pc) => (
                    <TableRow key={pc.pc_id}>
                    <TableCell
                        sx={{ color: theme.palette.text.black }}
                    >{pc.pc_id}</TableCell>
                    <TableCell
                        sx={{ color: theme.palette.text.black }}
                    >{pc.ip_address}</TableCell>
                    <TableCell
                        sx={{ color: theme.palette.text.black }}
                    >{pc.mac_address}</TableCell>
                    <TableCell
                        sx={{ color: theme.palette.text.black }}
                    >{pc.current_state}</TableCell>
                    <TableCell
                        sx={{ color: theme.palette.text.black }}
                    >{pc.present_user_id || '-'}</TableCell>
                    <TableCell
                      sx={{ color: pc.access_flag ? theme.palette.success.main : theme.palette.error.main }}
                    >
                      {pc.access_flag ? '허용' : '차단'}
                    </TableCell>
                    <TableCell>
                      <button
                        style={{
                          background: pc.access_flag ? theme.palette.error.main : theme.palette.success.main,
                          color: theme.palette.common.white,
                          border: 'none',
                          borderRadius: 4,
                          padding: '4px 12px',
                          cursor: 'pointer',
                          fontWeight: 600,
                        }}
                        onClick={() => BlockPCNetwork(pc.pc_id, !pc.access_flag)}
                      >
                        {pc.access_flag ? '차단' : '해제'}
                      </button>
                    </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
        );
};

const PcsStatusPage = () => {
    const [refreshKey, setRefreshKey] = useState(0);
    return (
        <Box flex={{ xs: '1 1 100%', md: '0 0 60%' }}>
            <CommonCard 
                title={
                    <Box display="flex" alignItems="center" justifyContent="center" position="relative">
                        <Box flex={1} textAlign="center" fontWeight={700} fontSize={20}>
                            PC 상태 현황
                        </Box>
                        <Box position="absolute" right={0} top={0} height="100%" display="flex" alignItems="center">
                            <button
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    padding: 0,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                }}
                                onClick={() => setRefreshKey((k) => k + 1)}
                                aria-label="새로고침"
                            >
                                <RefreshIcon fontSize="small" />
                            </button>
                        </Box>
                    </Box>
                }
            >
                <Box height={400} overflow="auto">
                    <PcsStatusTable key={refreshKey} />
                </Box>
            </CommonCard>
        </Box>
    );
};

export default PcsStatusPage;
