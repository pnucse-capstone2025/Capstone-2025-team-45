// MaliciousDetectionsOverTimeChartMock.jsx
import React from 'react';
import { Box } from '@mui/material';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    LineElement,
    PointElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend
} from 'chart.js';
import { format, parseISO } from 'date-fns';
import { useTheme } from '@mui/material/styles';
import { useNavigate, useParams } from 'react-router-dom';
import {get_anomaly_count_by_week} from '../../../api/dashboard';

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend);

const MaliciousDetectionsOverTimeChartMock = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const { oid } = useParams();

    const [trendData, setTrendData] = React.useState([]);
    React.useEffect(() => {
        async function fetchData() {
            try {
                const res = await get_anomaly_count_by_week(oid);
                setTrendData(Array.isArray(res) ? res : []);
            } catch (e) {
                setTrendData([]);
            }
        }
        fetchData();
    }, [oid]);

    const labels = trendData.map(item => item.week || '');
    const dataPoints = trendData.map(item => Number.isFinite(item?.anomaly_user_count) ? Number(item.anomaly_user_count) : null);
    const historyIds = trendData.map(item => item.history_id || null);

    const chartData = {
        labels,
        datasets: [
            {
                label: 'Malicious Users Detected',
                data: dataPoints,
                fill: false,
                borderColor: theme.palette.error.main,
                backgroundColor: theme.palette.error.main,
                tension: 0.3,
                pointRadius: 5,
                pointHoverRadius: 7,
                spanGaps: true
            }
        ]
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'top' },
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: (context) => {
                        const index = context.dataIndex;
                        const value = context.raw;
                        const week = labels[index];
                        const hid = historyIds[index];
                        return [
                            `Detections: ${value ?? 0}`,
                            week ? `Week: ${week}` : null,
                            hid ? `History ID: ${hid}` : null
                        ].filter(Boolean);
                    }
                }
            }
        },
        onClick: (event, elements) => {
            if (elements.length > 0) {
                const index = elements[0].index;
                const hid = historyIds[index];
                if (hid) {
                    navigate(`/RMF/${oid}/Incidents/history/${hid}`);
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: 'Detections' },
                ticks: { precision: 0, stepSize: 1 }
            },
            x: { title: { display: true, text: 'Week' } }
        }
    };

    return (
        <Box sx={{ width: '100%', height: '100%', minWidth: 0 }}>
            <Line data={chartData} options={{ ...options, responsive: true, maintainAspectRatio: false }} />
        </Box>
    );
};

export default MaliciousDetectionsOverTimeChartMock;
