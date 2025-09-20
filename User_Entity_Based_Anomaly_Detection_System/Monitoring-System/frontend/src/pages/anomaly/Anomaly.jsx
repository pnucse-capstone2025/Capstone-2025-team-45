import React, { useState, useEffect } from 'react';
import { Box, Button, TextField, Table, TableBody, TableCell, TableHead, TableRow, Modal, Typography, CircularProgress, IconButton, TablePagination } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip as ChartTooltip, Legend } from 'chart.js'; // Chart.js의 Tooltip을 별칭으로 변경
import { fetchAnomalyDetection, fetchAnomalyDetectionDetails, fetchAnomalyDetectionHistories } from '../../services/AnomalyDetection';
import { useParams } from 'react-router-dom';
import CommonCard from '../../components/common/card/CommonCard';
import { useTheme } from '@emotion/react';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import Tooltip from '@mui/material/Tooltip'; // MUI의 Tooltip을 유지
import RefreshIcon from '@mui/icons-material/Refresh';

ChartJS.register(ArcElement, ChartTooltip, Legend);

const Anomaly = () => {
  const { oid } = useParams();
  const theme = useTheme();
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [result, setResult] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDetails, setUserDetails] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage] = useState(6);
  const [history, setHistory] = useState([]);
  const [selectedHistory, setSelectedHistory] = useState(null);
  const [historyModalOpen, setHistoryModalOpen] = useState(false);

  const scenarioInfo = {
    1: {
      title: 'Class 1',
      description: ' 내부 정보 외부 유출: 퇴사를 앞두고 민감 정보를 외부에 대량 유출하는 행위'
    },
    2: {
      title: 'Class 2',
      description: '핵심 자산 절취: 이직 등을 위해 회사의 핵심 기술, 고객 정보 등을 훔치는 행위'
    },
    3: {
      title: 'Class 3',
      description: '시스템 파괴 및 사보타주: 악성코드나 계정 탈취로 시스템을 파괴하거나 업무를 마비시키는 행위'
    }
  };

  const handleFetch = async () => {
    setLoading(true);
    try {
      const data = await fetchAnomalyDetection({
        organizationId: oid,
        startDate,
        endDate,
      });
      setResult(data.results);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUserClick = async (userId) => {
    setSelectedUser(userId);
    setModalOpen(true);
    try {
      const details = await fetchAnomalyDetectionDetails(userId, startDate, endDate);
      setUserDetails(details);
    } catch (e) {
      alert(e.message);
    }
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedUser(null);
    setUserDetails([]);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  // Fetch anomaly detection histories
  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await fetchAnomalyDetectionHistories(oid);
      setHistory(data.results);
    } catch (e) {
      alert('탐지 히스토리를 가져오는 데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [oid]);

  const handleHistoryClick = (historyItem) => {
    setSelectedHistory(historyItem);
    setHistoryModalOpen(true);
  };

  const handleCloseHistoryModal = () => {
    setHistoryModalOpen(false);
    setSelectedHistory(null);
  };

  return (
    <Box p={4}>
      <CommonCard title="이상 사용자 탐지">
        <Box mb={2} display="flex" gap={2} alignItems="center">
          <TextField
            label="시작 날짜"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <TextField
            label="끝 날짜"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
          <Box display="flex" alignItems="center" gap={1}>
            <Button
              variant="contained"
              onClick={handleFetch}
              disabled={loading}
            >
              {loading ? '탐지 중...' : '탐지 수행'}
            </Button>
            {loading && (
              <>
                <CircularProgress size={24} />
                <Typography variant="body2" color="text.secondary">
                  3~4분 정도 소요됩니다
                </Typography>
              </>
            )}
          </Box>
        </Box>

        <Table>
          <TableHead
            sx={{
              '& th': {
                backgroundColor: 'background.default', // 헤드의 백그라운드 컬러를 검은색으로 설정
                color: theme.palette.text.white, // 텍스트 색상을 흰색으로 설정
                fontWeight: 'bold', // 텍스트를 볼드 처리
                textAlign: 'center', // 헤드 텍스트 가운데 정렬
              },
            }}
          >
            <TableRow>
              <TableCell>이상 사용자 ID</TableCell>
              <TableCell>
                <Box display="flex" alignItems="center" justifyContent="center"> {/* 가운데 정렬 */}
                  예측 클래스
                  <Tooltip
                    title={
                      <Box>
                        {Object.entries(scenarioInfo).map(([key, info]) => (
                          <Box key={key} mb={1}>
                            <Typography variant="subtitle2" fontWeight="bold">{info.title}</Typography>
                            <Typography variant="body2">{info.description}</Typography>
                          </Box>
                        ))}
                      </Box>
                    }
                    arrow
                  >
                    <InfoOutlinedIcon sx={{ ml: 1, cursor: 'pointer', color: theme.palette.text.white }} />
                  </Tooltip>
                </Box>
              </TableCell>
              <TableCell>이상 확률</TableCell>
              <TableCell>클래스별 확률</TableCell>
            </TableRow>
          </TableHead>
          <TableBody
            sx={{
              '& td': { color: theme.palette.text.black, textAlign: 'center' }, // 모든 값 가운데 정렬
            }}
          >
            {Object.entries(result).length > 0 ? (
              Object.entries(result).map(([uid, info]) => (
                <TableRow key={uid}>
                  <TableCell align="left">
                    <Typography
                      sx={{ cursor: 'pointer', color: 'blue' }}
                      onClick={() => handleUserClick(uid)}
                    >
                      {uid}
                    </Typography>
                  </TableCell>
                  <TableCell>{info.pred_class}</TableCell>
                  <TableCell>{(info.p_anomaly * 100).toFixed(1)}%</TableCell>
                  <TableCell>
                    <Box display="flex" justifyContent="center"> {/* 파이차트 가운데 정렬 */}
                      <Pie
                        data={{
                          labels: Object.keys(info.proba),
                          datasets: [{
                            data: Object.values(info.proba),
                            backgroundColor: ['#D9D9D9', '#FFB703', '#FB8500', '#D00000'],
                          }]
                        }}
                        options={{
                          plugins: { legend: { display: true } },
                          responsive: false,
                        }}
                      />
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} sx={{ textAlign: 'center', color: theme.palette.text.secondary }}>
                  조회된 이상 사용자가 없습니다. 다른 날짜 범위를 선택해보세요.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CommonCard>

      {/* 사용자 행동 로그 모달 */}
      <Modal open={modalOpen} onClose={handleCloseModal}>
        <Box
          p={4}
          bgcolor="white"
          borderRadius={2}
          sx={{
            width: '80%',
            maxWidth: '600px',
            margin: 'auto',
            marginTop: '10%',
            position: 'relative',
            boxShadow: 3,
          }}
        >
          <IconButton
            onClick={handleCloseModal}
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              color: theme.palette.text.black, // 닫기 버튼 색상 설정
            }}
          >
            <CloseIcon />
          </IconButton>
          <Typography variant="h6" fontWeight="bold" mb={2}>사용자 행동 로그</Typography> {/* 제목 볼드 처리 */}
          {userDetails.length > 0 ? (
            <>
              <Table>
                <TableHead
                  sx={{
                    '& th': {
                      backgroundColor: 'background.default', // 헤드의 백그라운드 컬러를 검은색으로 설정
                      color: theme.palette.text.white, // 텍스트 색상을 흰색으로 설정
                      fontWeight: 'bold', // 텍스트를 볼드 처리
                    },
                  }}
                >
                  <TableRow>
                    <TableCell >이벤트 ID</TableCell>
                    <TableCell >PC</TableCell>
                    <TableCell >시각</TableCell>
                    <TableCell >이벤트 타입</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {userDetails.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((log) => (
                    <TableRow key={log.event_id}>
                      <TableCell sx={{ color: theme.palette.text.black }}>{log.event_id}</TableCell>
                      <TableCell sx={{ color: theme.palette.text.black }}>{log.pc_id}</TableCell>
                      <TableCell sx={{ color: theme.palette.text.black }}>{log.timestamp}</TableCell>
                      <TableCell sx={{ color: theme.palette.text.black }}>{log.event_type}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <TablePagination
                rowsPerPageOptions={[]} // 한 번에 볼 수 있는 row 수 선택 옵션 제거
                component="div"
                count={userDetails.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                sx={{
                  '.MuiTablePagination-toolbar': {
                    backgroundColor: 'background.default',
                    color: theme.palette.text.white, // 페이지 안내 문구 색상 설정
                  },
                  '.MuiTablePagination-actions': {
                    color: theme.palette.text.white, // 버튼 색상 설정
                  },
                }}
              />
            </>
          ) : (
            <Typography sx={{ color: theme.palette.text.black }}>데이터를 불러올 수 없습니다.</Typography>
          )}
        </Box>
      </Modal>
      
      <Box mt={4} />   {/* 두 컴포넌트 사이 간격 추가 */}

      {/* 이상 탐지 결과 조회 카드 */}
      <CommonCard title="이상 탐지 결과 조회">
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">이상 탐지 결과 조회</Typography>
          <RefreshIcon
            onClick={fetchHistory}
            style={{
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '20px', // 아이콘 크기 줄이기
              color: loading ? '#a1a1aa' : '#000000', // 로딩 중일 때는 회색, 기본은 검정색
              pointerEvents: loading ? 'none' : 'auto', // 로딩 중일 때 클릭 비활성화
            }}
          />
        </Box>
        <Table>
          <TableHead
            sx={{
              '& th': {
                backgroundColor: 'background.default', // 헤드의 백그라운드 컬러를 검은색으로 설정
                color: theme.palette.text.white, // 텍스트 색상을 흰색으로 설정
                fontWeight: 'bold', // 텍스트를 볼드 처리
              },
            }}
          >
            <TableRow>
              <TableCell>스캔 ID</TableCell>
              <TableCell>스캔 시각</TableCell>
              <TableCell>스캔 대상 기간</TableCell>
              <TableCell>세부 사항</TableCell>
            </TableRow>
          </TableHead>
          <TableBody
            sx={{
              '& td': { color: theme.palette.text.black },
            }}
          >
            {history.map((item) => (
              <TableRow key={item.anomaly_detection_history_id}>
                <TableCell>{item.anomaly_detection_history_id}</TableCell>
                <TableCell>{item.run_timestamp}</TableCell>
                <TableCell>{`${item.start_date} ~ ${item.end_date}`}</TableCell>
                <TableCell>
                  <Button variant="outlined" onClick={() => handleHistoryClick(item)}>
                    세부 사항 보기
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CommonCard>

      {/* Modal for "이상 탐지 결과 조회" 세부사항 모달 */}
      <Modal open={historyModalOpen} onClose={handleCloseHistoryModal}>
        <Box
          p={4}
          bgcolor="white"
          borderRadius={2}
          sx={{
            width: '80%',
            maxWidth: '600px',
            margin: 'auto',
            marginTop: '10%',
            position: 'relative',
            boxShadow: 3,
          }}
        >
          <IconButton
            onClick={handleCloseHistoryModal}
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              color: theme.palette.text.black,
            }}
          >
            <CloseIcon />
          </IconButton>
          <Typography variant="h6" fontWeight="bold" mb={2}>세부 사항</Typography>
          {selectedHistory && Object.keys(JSON.parse(selectedHistory.results)).length > 0 ? (
            <>
              <Table>
                <TableHead
                  sx={{
                    '& th': {
                      backgroundColor: 'background.default', 
                      color: theme.palette.text.white, 
                      fontWeight: 'bold', 
                    },
                  }}
                >
                  <TableRow>
                    <TableCell>사용자 ID</TableCell>
                    <TableCell>예측 클래스</TableCell>
                    <TableCell>이상 확률</TableCell>
                    <TableCell>클래스별 확률</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(JSON.parse(selectedHistory.results))
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map(([uid, info]) => (
                      <TableRow key={uid}>
                        <TableCell sx={{ color: theme.palette.text.black }}>{uid}</TableCell>
                        <TableCell sx={{ color: theme.palette.text.black }}>{info.pred_class}</TableCell>
                        <TableCell sx={{ color: theme.palette.text.black }}>{(info.p_anomaly * 100).toFixed(1)}%</TableCell>
                        <TableCell sx={{ color: theme.palette.text.black }}>
                          {Object.entries(info.proba).map(([classId, prob]) => (
                            <Typography key={classId}>{`Class ${classId}: ${(prob * 100).toFixed(1)}%`}</Typography>
                          ))}
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
              <TablePagination
                rowsPerPageOptions={[]} // 한 번에 볼 수 있는 row 수 선택 옵션 제거
                component="div"
                count={Object.keys(JSON.parse(selectedHistory.results)).length}
                rowsPerPage={rowsPerPage} // 한 페이지에 표시할 행 수를 6으로 고정
                page={page}
                onPageChange={handleChangePage}
                sx={{
                  '.MuiTablePagination-toolbar': {
                    backgroundColor: 'background.default',
                    color: theme.palette.text.white, // 페이지 안내 문구 색상 설정
                  },
                  '.MuiTablePagination-actions': {
                    color: theme.palette.text.white, // 버튼 색상 설정
                  },
                }}
              />
            </>
          ) : (
            <Typography sx={{ color: theme.palette.text.secondary, textAlign: 'center', mt: 2 }}>
              조회된 탐지 결과가 없습니다. 다른 탐지 기록을 선택해보세요.
            </Typography>
          )}
        </Box>
      </Modal>
    </Box>
  );
};

export default Anomaly;