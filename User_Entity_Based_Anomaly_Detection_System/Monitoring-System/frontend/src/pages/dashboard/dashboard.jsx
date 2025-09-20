import React from 'react';
import { Box } from '@mui/material';
import PcLogonRatioCardMock from './statisticComponents/PcLogonRatioCard';
import CommonCard from '../../components/common/card/CommonCard';
import MaliciousDetectionsOverTimeChart from './statisticComponents/MaliciousDetectionsOverTimeChart';
import AnomalyAlertListener from '../../components/Alert/AnomalyAlertListener';
import WeeklyStackedLogByMonth from './statisticComponents/WeeklyStackedLogByMonth';
import { useParams } from 'react-router-dom';
import AnomalyEmployeeList from './statisticComponents/AnomalyEmployeeList';
import BlockingNetworkHistory from './statisticComponents/BlockingNetworkHistory';
const Dashboard = () => {
  const { oid } = useParams();
  return (
    <>
    <Box>
          <Box
        display="flex"
        flexDirection={{ xs: 'column', md: 'row' }}
        gap={2}
        alignItems="stretch"
      >
        <Box flex={{ xs: '1 1 100%', md: '0 0 30%' }}>
          <PcLogonRatioCardMock />
        </Box>
        
        <Box flex={{ xs: '1 1 100%', md: '0 0 65%' }}>
          <CommonCard title="주간 이상 사용자 탐지 현황">
            <Box height={250}>
              <MaliciousDetectionsOverTimeChart />
            </Box>
          </CommonCard>
        </Box>
        
      </Box>
      <Box mt={2} display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={2}>
        <Box flex={1}>
          <CommonCard title="월별/주차별 로그 유형 집계">
            <Box height={320}>
              <WeeklyStackedLogByMonth />
            </Box>
          </CommonCard>
        </Box>
        <Box flex={{ xs: '1 1 100%', md: '0 0 30%' }}>
            <Box height={250}>
              <BlockingNetworkHistory />
            </Box>
        </Box>
        <Box flex={1}>
          <CommonCard title="이상 사용자 목록">
            <AnomalyEmployeeList />
          </CommonCard>
        </Box>
      </Box>
    </Box>
  
    </>
  );
};

export default Dashboard;